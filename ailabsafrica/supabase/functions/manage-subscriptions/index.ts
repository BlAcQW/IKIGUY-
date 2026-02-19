import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

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
  user_id: string;
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
  id: string;
  user_id: string;
  subscription_id: string;
  feature_name: string;
  usage_count: number;
  limit_count?: number;
  reset_date: string;
}

interface BillingInvoice {
  id: string;
  user_id: string;
  subscription_id: string;
  amount: number;
  currency: string;
  status: 'draft' | 'open' | 'paid' | 'uncollectible' | 'void';
  stripe_invoice_id?: string;
  stripe_payment_intent_id?: string;
  due_date: string;
  paid_at?: string;
  invoice_pdf_url?: string;
  hosted_invoice_url?: string;
}

interface PaymentMethod {
  id: string;
  user_id: string;
  stripe_payment_method_id: string;
  type: 'card' | 'bank_account' | 'sepa_debit' | 'ideal' | 'sofort';
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
  is_default: boolean;
  is_active: boolean;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Create Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get user from JWT
    const authHeader = req.headers.get('Authorization')!;
    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);

    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { action, data } = await req.json();

    switch (action) {
      case 'get_plans':
        return await getPlans(supabase);

      case 'get_current_subscription':
        return await getCurrentSubscription(supabase, user.id);

      case 'create_subscription':
        return await createSubscription(supabase, user.id, data);

      case 'cancel_subscription':
        return await cancelSubscription(supabase, user.id, data);

      case 'update_subscription':
        return await updateSubscription(supabase, user.id, data);

      case 'get_usage':
        return await getUsage(supabase, user.id);

      case 'increment_usage':
        return await incrementUsage(supabase, user.id, data);

      case 'get_invoices':
        return await getInvoices(supabase, user.id);

      case 'get_payment_methods':
        return await getPaymentMethods(supabase, user.id);

      case 'add_payment_method':
        return await addPaymentMethod(supabase, user.id, data);

      case 'remove_payment_method':
        return await removePaymentMethod(supabase, user.id, data);

      case 'set_default_payment_method':
        return await setDefaultPaymentMethod(supabase, user.id, data);

      case 'check_feature_access':
        return await checkFeatureAccess(supabase, user.id, data);

      case 'get_subscription_analytics':
        return await getSubscriptionAnalytics(supabase);

      default:
        return new Response(
          JSON.stringify({ error: 'Invalid action' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
    }
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

async function getPlans(supabase: any) {
  const { data, error } = await supabase
    .from('subscription_plans')
    .select('*')
    .eq('is_active', true)
    .order('sort_order');

  if (error) throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function getCurrentSubscription(supabase: any, userId: string) {
  const { data, error } = await supabase
    .from('user_subscriptions')
    .select(`
      *,
      subscription_plans (
        id,
        name,
        description,
        price,
        currency,
        billing_cycle,
        features,
        limits
      )
    `)
    .eq('user_id', userId)
    .in('status', ['active', 'trialing', 'past_due'])
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  if (error && error.code !== 'PGRST116') throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function createSubscription(supabase: any, userId: string, data: { plan_id: string }) {
  // Get plan details
  const { data: plan, error: planError } = await supabase
    .from('subscription_plans')
    .select('*')
    .eq('id', data.plan_id)
    .single();

  if (planError) throw planError;

  // Calculate billing period
  const now = new Date();
  let periodEnd = new Date(now);
  
  switch (plan.billing_cycle) {
    case 'monthly':
      periodEnd.setMonth(periodEnd.getMonth() + 1);
      break;
    case 'yearly':
      periodEnd.setFullYear(periodEnd.getFullYear() + 1);
      break;
    case 'weekly':
      periodEnd.setDate(periodEnd.getDate() + 7);
      break;
    case 'daily':
      periodEnd.setDate(periodEnd.getDate() + 1);
      break;
  }

  // Create subscription
  const subscriptionData = {
    user_id: userId,
    plan_id: data.plan_id,
    status: 'active',
    current_period_start: now.toISOString(),
    current_period_end: periodEnd.toISOString(),
    cancel_at_period_end: false,
  };

  const { data: subscription, error } = await supabase
    .from('user_subscriptions')
    .insert(subscriptionData)
    .select()
    .single();

  if (error) throw error;

  // Log subscription event
  await supabase
    .from('subscription_events')
    .insert({
      user_id: userId,
      subscription_id: subscription.id,
      event_type: 'subscription_created',
      event_data: { plan_id: data.plan_id, plan_name: plan.name },
    });

  return new Response(
    JSON.stringify({ data: subscription }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function cancelSubscription(supabase: any, userId: string, data: { subscription_id: string }) {
  const { data: subscription, error } = await supabase
    .from('user_subscriptions')
    .update({
      status: 'cancelled',
      cancel_at_period_end: true,
      cancelled_at: new Date().toISOString(),
    })
    .eq('id', data.subscription_id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) throw error;

  // Log cancellation event
  await supabase
    .from('subscription_events')
    .insert({
      user_id: userId,
      subscription_id: data.subscription_id,
      event_type: 'subscription_cancelled',
      event_data: { cancelled_at: new Date().toISOString() },
    });

  return new Response(
    JSON.stringify({ data: subscription }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function updateSubscription(supabase: any, userId: string, data: Partial<UserSubscription>) {
  const { data: subscription, error } = await supabase
    .from('user_subscriptions')
    .update(data)
    .eq('id', data.id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) throw error;

  return new Response(
    JSON.stringify({ data: subscription }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function getUsage(supabase: any, userId: string) {
  const { data, error } = await supabase
    .from('subscription_usage')
    .select('*')
    .eq('user_id', userId)
    .gte('reset_date', new Date().toISOString().split('T')[0])
    .order('feature_name');

  if (error) throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function incrementUsage(supabase: any, userId: string, data: { feature_name: string; increment_amount?: number }) {
  const incrementAmount = data.increment_amount || 1;
  const currentDate = new Date().toISOString().split('T')[0];

  // Get or create usage record
  const { data: existingUsage, error: selectError } = await supabase
    .from('subscription_usage')
    .select('*')
    .eq('user_id', userId)
    .eq('feature_name', data.feature_name)
    .eq('reset_date', currentDate)
    .single();

  if (selectError && selectError.code !== 'PGRST116') throw selectError;

  let usageData;
  if (existingUsage) {
    // Update existing usage
    const { data: updatedUsage, error: updateError } = await supabase
      .from('subscription_usage')
      .update({ usage_count: existingUsage.usage_count + incrementAmount })
      .eq('id', existingUsage.id)
      .select()
      .single();

    if (updateError) throw updateError;
    usageData = updatedUsage;
  } else {
    // Create new usage record
    const { data: newUsage, error: insertError } = await supabase
      .from('subscription_usage')
      .insert({
        user_id: userId,
        feature_name: data.feature_name,
        usage_count: incrementAmount,
        reset_date: currentDate,
      })
      .select()
      .single();

    if (insertError) throw insertError;
    usageData = newUsage;
  }

  return new Response(
    JSON.stringify({ data: usageData }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function getInvoices(supabase: any, userId: string) {
  const { data, error } = await supabase
    .from('billing_invoices')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(20);

  if (error) throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function getPaymentMethods(supabase: any, userId: string) {
  const { data, error } = await supabase
    .from('payment_methods')
    .select('*')
    .eq('user_id', userId)
    .eq('is_active', true)
    .order('is_default', { ascending: false });

  if (error) throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function addPaymentMethod(supabase: any, userId: string, data: Partial<PaymentMethod>) {
  const { data: paymentMethod, error } = await supabase
    .from('payment_methods')
    .insert({
      user_id: userId,
      ...data,
    })
    .select()
    .single();

  if (error) throw error;

  return new Response(
    JSON.stringify({ data: paymentMethod }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function removePaymentMethod(supabase: any, userId: string, data: { id: string }) {
  const { error } = await supabase
    .from('payment_methods')
    .update({ is_active: false })
    .eq('id', data.id)
    .eq('user_id', userId);

  if (error) throw error;

  return new Response(
    JSON.stringify({ success: true }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function setDefaultPaymentMethod(supabase: any, userId: string, data: { id: string }) {
  // First, remove default from all payment methods
  await supabase
    .from('payment_methods')
    .update({ is_default: false })
    .eq('user_id', userId);

  // Then set the new default
  const { data: paymentMethod, error } = await supabase
    .from('payment_methods')
    .update({ is_default: true })
    .eq('id', data.id)
    .eq('user_id', userId)
    .select()
    .single();

  if (error) throw error;

  return new Response(
    JSON.stringify({ data: paymentMethod }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function checkFeatureAccess(supabase: any, userId: string, data: { feature_name: string }) {
  // Get user's current subscription
  const { data: subscription, error: subError } = await supabase
    .from('user_subscriptions')
    .select(`
      *,
      subscription_plans (
        features,
        limits
      )
    `)
    .eq('user_id', userId)
    .in('status', ['active', 'trialing', 'past_due'])
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  if (subError && subError.code !== 'PGRST116') throw subError;

  if (!subscription) {
    return new Response(
      JSON.stringify({ data: { has_access: false, reason: 'No active subscription' } }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  const plan = subscription.subscription_plans;
  const featureLimit = plan.limits[data.feature_name];
  const hasFeature = plan.features[data.feature_name];

  if (!hasFeature) {
    return new Response(
      JSON.stringify({ data: { has_access: false, reason: 'Feature not included in plan' } }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  if (featureLimit === -1 || featureLimit === undefined) {
    return new Response(
      JSON.stringify({ data: { has_access: true, reason: 'Unlimited feature' } }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // Check current usage
  const currentDate = new Date().toISOString().split('T')[0];
  const { data: usage, error: usageError } = await supabase
    .from('subscription_usage')
    .select('usage_count')
    .eq('user_id', userId)
    .eq('feature_name', data.feature_name)
    .eq('reset_date', currentDate)
    .single();

  if (usageError && usageError.code !== 'PGRST116') throw usageError;

  const currentUsage = usage?.usage_count || 0;
  const hasAccess = currentUsage < featureLimit;

  return new Response(
    JSON.stringify({
      data: {
        has_access: hasAccess,
        reason: hasAccess ? 'Within limit' : 'Usage limit exceeded',
        current_usage: currentUsage,
        limit: featureLimit,
        remaining: Math.max(0, featureLimit - currentUsage),
      },
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

async function getSubscriptionAnalytics(supabase: any) {
  // This would typically be restricted to admin users
  const { data, error } = await supabase.rpc('get_subscription_analytics');

  if (error) throw error;

  return new Response(
    JSON.stringify({ data }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}
