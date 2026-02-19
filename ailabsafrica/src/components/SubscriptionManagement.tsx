import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import {
  Check, X, Star, CreditCard, Settings, BarChart3, Download, Upload, 
  Users, Zap, Shield, Globe, Clock, Calendar, DollarSign, TrendingUp,
  AlertCircle, CheckCircle, Loader2, RefreshCw, ExternalLink, Settings as SettingsIcon,
  CreditCard as CreditCardIcon, BarChart3 as BarChart3Icon, Users as UsersIcon,
  Zap as ZapIcon, Shield as ShieldIcon, Globe as GlobeIcon, Clock as ClockIcon,
  Calendar as CalendarIcon, DollarSign as DollarSignIcon, TrendingUp as TrendingUpIcon,
  AlertCircle as AlertCircleIcon, CheckCircle as CheckCircleIcon, Loader2 as Loader2Icon,
  RefreshCw as RefreshCwIcon, ExternalLink as ExternalLinkIcon, SettingsIcon as SettingsIcon2
} from 'lucide-react';

interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  billing_cycle: 'monthly' | 'yearly' | 'weekly' | 'daily';
  features: Record<string, any>;
  limits: Record<string, any>;
  is_active: boolean;
  is_popular: boolean;
  is_custom: boolean;
  sort_order: number;
}

interface UserSubscription {
  id: string;
  plan_id: string;
  status: 'active' | 'inactive' | 'cancelled' | 'past_due' | 'trialing' | 'unpaid';
  current_period_start: string;
  current_period_end: string;
  trial_start?: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
  cancelled_at?: string;
  stripe_subscription_id?: string;
  stripe_customer_id?: string;
}

interface SubscriptionUsage {
  feature_name: string;
  usage_count: number;
  limit_count?: number;
  reset_date: string;
}

interface BillingInvoice {
  id: string;
  amount: number;
  currency: string;
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void';
  due_date: string;
  paid_at?: string;
  invoice_pdf_url?: string;
  hosted_invoice_url?: string;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'bank_account' | 'sepa_debit' | 'ideal' | 'sofort';
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
  is_default: boolean;
  is_active: boolean;
}

const SubscriptionManagement: React.FC = () => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [usage, setUsage] = useState<SubscriptionUsage[]>([]);
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [showSubscribeDialog, setShowSubscribeDialog] = useState(false);
  const [showBillingDialog, setShowBillingDialog] = useState(false);
  const [showUsageDialog, setShowUsageDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('plans');
  const { toast } = useToast();

  useEffect(() => {
    loadSubscriptionData();
  }, []);

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);
      
      // Load subscription plans
      const { data: plansData, error: plansError } = await supabase
        .from('subscription_plans')
        .select('*')
        .eq('is_active', true)
        .order('sort_order');

      if (plansError) throw plansError;
      setPlans(plansData || []);

      // Load current subscription
      const { data: subscriptionData, error: subscriptionError } = await supabase
        .from('user_subscriptions')
        .select('*')
        .single();

      if (subscriptionError && subscriptionError.code !== 'PGRST116') {
        throw subscriptionError;
      }
      setCurrentSubscription(subscriptionData);

      // Load usage data
      const { data: usageData, error: usageError } = await supabase
        .from('subscription_usage')
        .select('*')
        .gte('reset_date', new Date().toISOString().split('T')[0]);

      if (usageError) throw usageError;
      setUsage(usageData || []);

      // Load invoices
      const { data: invoicesData, error: invoicesError } = await supabase
        .from('billing_invoices')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      if (invoicesError) throw invoicesError;
      setInvoices(invoicesData || []);

      // Load payment methods
      const { data: paymentMethodsData, error: paymentMethodsError } = await supabase
        .from('payment_methods')
        .select('*')
        .eq('is_active', true);

      if (paymentMethodsError) throw paymentMethodsError;
      setPaymentMethods(paymentMethodsData || []);

    } catch (error) {
      console.error('Error loading subscription data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load subscription data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    setShowSubscribeDialog(true);
  };

  const handleConfirmSubscription = async () => {
    if (!selectedPlan) return;

    try {
      // Mock subscription creation - in real implementation, this would integrate with Stripe
      const { data, error } = await supabase
        .from('user_subscriptions')
        .insert({
          plan_id: selectedPlan.id,
          status: 'active',
          current_period_start: new Date().toISOString(),
          current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
        })
        .select()
        .single();

      if (error) throw error;

      setCurrentSubscription(data);
      setShowSubscribeDialog(false);
      setSelectedPlan(null);

      toast({
        title: 'Success',
        description: `Successfully subscribed to ${selectedPlan.name} plan`,
      });

      // Reload data
      await loadSubscriptionData();

    } catch (error) {
      console.error('Error creating subscription:', error);
      toast({
        title: 'Error',
        description: 'Failed to create subscription',
        variant: 'destructive',
      });
    }
  };

  const handleCancelSubscription = async () => {
    if (!currentSubscription) return;

    try {
      const { error } = await supabase
        .from('user_subscriptions')
        .update({
          status: 'cancelled',
          cancel_at_period_end: true,
          cancelled_at: new Date().toISOString(),
        })
        .eq('id', currentSubscription.id);

      if (error) throw error;

      toast({
        title: 'Success',
        description: 'Subscription cancelled successfully',
      });

      await loadSubscriptionData();

    } catch (error) {
      console.error('Error cancelling subscription:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel subscription',
        variant: 'destructive',
      });
    }
  };

  const getFeatureIcon = (featureName: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      assistants: <Users className="w-4 h-4" />,
      templates: <Zap className="w-4 h-4" />,
      api_calls: <Globe className="w-4 h-4" />,
      storage: <Shield className="w-4 h-4" />,
      support: <CheckCircle className="w-4 h-4" />,
      analytics: <BarChart3 className="w-4 h-4" />,
      integrations: <Settings className="w-4 h-4" />,
      team_collaboration: <Users className="w-4 h-4" />,
      advanced_features: <Zap className="w-4 h-4" />,
      custom_integrations: <Settings className="w-4 h-4" />,
      sla: <Shield className="w-4 h-4" />,
    };
    return iconMap[featureName] || <Check className="w-4 h-4" />;
  };

  const formatFeatureValue = (value: any) => {
    if (value === true) return 'Included';
    if (value === false) return 'Not included';
    if (value === -1) return 'Unlimited';
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    return 'Included';
  };

  const getUsagePercentage = (featureName: string) => {
    const usageItem = usage.find(u => u.feature_name === featureName);
    if (!usageItem || !usageItem.limit_count) return 0;
    return Math.min((usageItem.usage_count / usageItem.limit_count) * 100, 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Subscription Management</h1>
          <p className="text-muted-foreground">
            Manage your subscription, billing, and usage
          </p>
        </div>
        <Button onClick={loadSubscriptionData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Current Subscription Status */}
      {currentSubscription && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Current Subscription
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Plan</p>
                <p className="text-lg font-semibold">
                  {plans.find(p => p.id === currentSubscription.plan_id)?.name || 'Unknown Plan'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <Badge variant={currentSubscription.status === 'active' ? 'default' : 'secondary'}>
                  {currentSubscription.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Next Billing</p>
                <p className="text-lg font-semibold">
                  {new Date(currentSubscription.current_period_end).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button variant="outline" onClick={() => setShowBillingDialog(true)}>
                <CreditCard className="w-4 h-4 mr-2" />
                Billing
              </Button>
              <Button variant="outline" onClick={() => setShowUsageDialog(true)}>
                <BarChart3 className="w-4 h-4 mr-2" />
                Usage
              </Button>
              <Button variant="destructive" onClick={handleCancelSubscription}>
                Cancel Subscription
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="plans">Plans</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="plans" className="space-y-6">
          {/* Subscription Plans */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card key={plan.id} className={`relative ${plan.is_popular ? 'ring-2 ring-primary' : ''}`}>
                {plan.is_popular && (
                  <Badge className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                    <Star className="w-3 h-3 mr-1" />
                    Most Popular
                  </Badge>
                )}
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    {plan.name}
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        ${plan.price}
                        <span className="text-sm font-normal text-muted-foreground">
                          /{plan.billing_cycle}
                        </span>
                      </div>
                    </div>
                  </CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Features */}
                  <div className="space-y-2">
                    {Object.entries(plan.features).map(([feature, value]) => (
                      <div key={feature} className="flex items-center gap-2">
                        {getFeatureIcon(feature)}
                        <span className="text-sm">
                          {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                        </span>
                        <span className="text-sm font-medium">
                          {formatFeatureValue(value)}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Action Button */}
                  <Button 
                    className="w-full" 
                    variant={plan.is_popular ? 'default' : 'outline'}
                    onClick={() => handleSubscribe(plan)}
                    disabled={currentSubscription?.plan_id === plan.id}
                  >
                    {currentSubscription?.plan_id === plan.id ? 'Current Plan' : 'Subscribe'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6">
          {/* Payment Methods */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                Payment Methods
              </CardTitle>
            </CardHeader>
            <CardContent>
              {paymentMethods.length > 0 ? (
                <div className="space-y-2">
                  {paymentMethods.map((method) => (
                    <div key={method.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <CreditCard className="w-5 h-5" />
                        <div>
                          <p className="font-medium">
                            {method.card_brand} •••• {method.card_last4}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Expires {method.card_exp_month}/{method.card_exp_year}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {method.is_default && (
                          <Badge variant="secondary">Default</Badge>
                        )}
                        <Button variant="outline" size="sm">
                          Edit
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No payment methods added</p>
              )}
              <Button className="mt-4" variant="outline">
                <CreditCard className="w-4 h-4 mr-2" />
                Add Payment Method
              </Button>
            </CardContent>
          </Card>

          {/* Invoices */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                Recent Invoices
              </CardTitle>
            </CardHeader>
            <CardContent>
              {invoices.length > 0 ? (
                <div className="space-y-2">
                  {invoices.map((invoice) => (
                    <div key={invoice.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">
                          ${invoice.amount} {invoice.currency.toUpperCase()}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Due: {new Date(invoice.due_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={invoice.status === 'paid' ? 'default' : 'secondary'}>
                          {invoice.status}
                        </Badge>
                        {invoice.hosted_invoice_url && (
                          <Button variant="outline" size="sm" asChild>
                            <a href={invoice.hosted_invoice_url} target="_blank" rel="noopener noreferrer">
                              <Download className="w-4 h-4" />
                            </a>
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No invoices found</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          {/* Usage Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Usage Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {usage.map((usageItem) => (
                  <div key={usageItem.feature_name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {usageItem.feature_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {usageItem.usage_count}
                        {usageItem.limit_count && ` / ${usageItem.limit_count}`}
                      </span>
                    </div>
                    {usageItem.limit_count && (
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${getUsagePercentage(usageItem.feature_name)}%` }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Subscribe Dialog */}
      <Dialog open={showSubscribeDialog} onOpenChange={setShowSubscribeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Subscribe to {selectedPlan?.name}</DialogTitle>
            <DialogDescription>
              You're about to subscribe to the {selectedPlan?.name} plan for ${selectedPlan?.price}/{selectedPlan?.billing_cycle}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-2">Plan Features:</h4>
              <ul className="space-y-1">
                {selectedPlan && Object.entries(selectedPlan.features).map(([feature, value]) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-500" />
                    {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: {formatFeatureValue(value)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowSubscribeDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleConfirmSubscription}>
                Confirm Subscription
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Billing Dialog */}
      <Dialog open={showBillingDialog} onOpenChange={setShowBillingDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Billing & Payment</DialogTitle>
            <DialogDescription>
              Manage your billing information and payment methods
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Billing content would go here */}
            <p className="text-muted-foreground">
              Billing management interface would be implemented here with Stripe integration.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Usage Dialog */}
      <Dialog open={showUsageDialog} onOpenChange={setShowUsageDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Usage Analytics</DialogTitle>
            <DialogDescription>
              Detailed view of your subscription usage and limits
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Usage content would go here */}
            <p className="text-muted-foreground">
              Detailed usage analytics would be implemented here with charts and graphs.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SubscriptionManagement;
