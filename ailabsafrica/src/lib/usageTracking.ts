import { supabase } from '@/integrations/supabase/client';

export interface UsageSession {
  sessionId: string;
  assistantId: string;
  userId: string;
  communicationMedium: 'webrtc' | 'phone' | 'sms' | 'video';
  provider: 'vapi' | 'vonage' | 'other';
  region: string;
  startTime: Date;
  endTime?: Date;
  durationMinutes?: number;
  totalCost?: number;
  status: 'active' | 'completed' | 'failed';
  metadata?: Record<string, any>;
}

export interface PricingInfo {
  baseCostPerMinute: number;
  markupPercentage: number;
  finalCostPerMinute: number;
  currency: string;
}

export interface UsageAlert {
  alertType: 'low_balance' | 'high_usage' | 'bundle_expiry' | 'payment_due';
  thresholdValue: number;
  currentValue: number;
  message: string;
}

/**
 * Start a new usage tracking session
 */
export async function startUsageSession(
  sessionData: Omit<UsageSession, 'startTime' | 'status'>
): Promise<string> {
  try {
    const session: UsageSession = {
      ...sessionData,
      startTime: new Date(),
      status: 'active'
    };

    const { data, error } = await supabase
      .from('usage_tracking')
      .insert({
        user_id: session.userId,
        assistant_id: session.assistantId,
        session_id: session.sessionId,
        start_time: session.startTime.toISOString(),
        communication_medium: session.communicationMedium,
        provider: session.provider,
        region: session.region,
        status: session.status,
        metadata: session.metadata || {}
      })
      .select('id')
      .single();

    if (error) throw error;
    return data.id;
  } catch (error) {
    console.error('Error starting usage session:', error);
    throw error;
  }
}

/**
 * End a usage tracking session and calculate costs
 */
export async function endUsageSession(
  sessionId: string,
  durationMinutes: number,
  metadata?: Record<string, any>
): Promise<void> {
  try {
    // Get session data
    const { data: session, error: sessionError } = await supabase
      .from('usage_tracking')
      .select('*')
      .eq('session_id', sessionId)
      .single();

    if (sessionError) throw sessionError;

    // Get pricing for the region and communication medium
    const pricing = await getPricingForRegion(
      session.region,
      session.communication_medium,
      session.provider
    );

    // Calculate total cost
    const totalCost = durationMinutes * pricing.finalCostPerMinute;

    // Update session with end time and costs
    const { error: updateError } = await supabase
      .from('usage_tracking')
      .update({
        end_time: new Date().toISOString(),
        duration_minutes: durationMinutes,
        cost_per_minute: pricing.finalCostPerMinute,
        total_cost: totalCost,
        status: 'completed',
        base_cost_per_minute: pricing.baseCostPerMinute,
        markup_percentage: pricing.markupPercentage,
        final_cost_per_minute: pricing.finalCostPerMinute,
        currency: pricing.currency,
        metadata: { ...session.metadata, ...metadata },
        updated_at: new Date().toISOString()
      })
      .eq('session_id', sessionId);

    if (updateError) throw updateError;

    // Deduct usage from wallet
    await deductUsageFromWallet(
      session.user_id,
      durationMinutes,
      session.assistant_id,
      sessionId,
      session.communication_medium,
      session.provider,
      session.region
    );

  } catch (error) {
    console.error('Error ending usage session:', error);
    throw error;
  }
}

/**
 * Get pricing information for a specific region and communication medium
 */
export async function getPricingForRegion(
  region: string,
  communicationMedium: string,
  provider: string = 'vapi'
): Promise<PricingInfo> {
  try {
    const { data, error } = await supabase
      .rpc('get_pricing_for_region', {
        p_region: region,
        p_communication_medium: communicationMedium,
        p_provider: provider
      });

    if (error) throw error;

    if (data && data.length > 0) {
      const pricing = data[0];
      return {
        baseCostPerMinute: pricing.base_cost_per_minute,
        markupPercentage: pricing.markup_percentage,
        finalCostPerMinute: pricing.final_cost_per_minute,
        currency: pricing.currency
      };
    }

    // Return default pricing if no specific pricing found
    return {
      baseCostPerMinute: 0.05,
      markupPercentage: 30.0,
      finalCostPerMinute: 0.065,
      currency: 'USD'
    };
  } catch (error) {
    console.error('Error getting pricing for region:', error);
    // Return default pricing on error
    return {
      baseCostPerMinute: 0.05,
      markupPercentage: 30.0,
      finalCostPerMinute: 0.065,
      currency: 'USD'
    };
  }
}

/**
 * Deduct usage from user's wallet
 */
export async function deductUsageFromWallet(
  userId: string,
  minutes: number,
  assistantId: string,
  sessionId: string,
  communicationMedium: string = 'webrtc',
  provider: string = 'vapi',
  region: string = 'GH'
): Promise<void> {
  try {
    const { error } = await supabase
      .rpc('deduct_usage_with_dynamic_pricing', {
        p_user_id: userId,
        p_minutes: minutes,
        p_assistant_id: assistantId,
        p_session_id: sessionId,
        p_communication_medium: communicationMedium,
        p_provider: provider,
        p_region: region
      });

    if (error) throw error;
  } catch (error) {
    console.error('Error deducting usage from wallet:', error);
    throw error;
  }
}

/**
 * Get user's current wallet balance
 */
export async function getWalletBalance(userId: string): Promise<number> {
  try {
    const { data, error } = await supabase
      .from('wallets')
      .select('balance')
      .eq('user_id', userId)
      .single();

    if (error) throw error;
    return data?.balance || 0;
  } catch (error) {
    console.error('Error getting wallet balance:', error);
    return 0;
  }
}

/**
 * Create a usage alert
 */
export async function createUsageAlert(alert: UsageAlert & { userId: string }): Promise<string> {
  try {
    const { data, error } = await supabase
      .rpc('create_usage_alert', {
        p_user_id: alert.userId,
        p_alert_type: alert.alertType,
        p_threshold_value: alert.thresholdValue,
        p_current_value: alert.currentValue,
        p_message: alert.message
      });

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('Error creating usage alert:', error);
    throw error;
  }
}

/**
 * Get user's usage statistics
 */
export async function getUserUsageStats(userId: string): Promise<{
  totalMinutes: number;
  totalCost: number;
  sessionsCount: number;
  averageSessionLength: number;
  usageByMedium: Record<string, { minutes: number; cost: number; sessions: number }>;
}> {
  try {
    const { data, error } = await supabase
      .from('usage_tracking')
      .select('communication_medium, duration_minutes, total_cost')
      .eq('user_id', userId)
      .eq('status', 'completed');

    if (error) throw error;

    const stats = {
      totalMinutes: 0,
      totalCost: 0,
      sessionsCount: data?.length || 0,
      averageSessionLength: 0,
      usageByMedium: {} as Record<string, { minutes: number; cost: number; sessions: number }>
    };

    if (data) {
      data.forEach(record => {
        const minutes = record.duration_minutes || 0;
        const cost = record.total_cost || 0;
        const medium = record.communication_medium || 'webrtc';

        stats.totalMinutes += minutes;
        stats.totalCost += cost;

        if (!stats.usageByMedium[medium]) {
          stats.usageByMedium[medium] = { minutes: 0, cost: 0, sessions: 0 };
        }

        stats.usageByMedium[medium].minutes += minutes;
        stats.usageByMedium[medium].cost += cost;
        stats.usageByMedium[medium].sessions += 1;
      });

      stats.averageSessionLength = stats.sessionsCount > 0 
        ? stats.totalMinutes / stats.sessionsCount 
        : 0;
    }

    return stats;
  } catch (error) {
    console.error('Error getting user usage stats:', error);
    return {
      totalMinutes: 0,
      totalCost: 0,
      sessionsCount: 0,
      averageSessionLength: 0,
      usageByMedium: {}
    };
  }
}

/**
 * Get user's active usage sessions
 */
export async function getActiveUsageSessions(userId: string): Promise<UsageSession[]> {
  try {
    const { data, error } = await supabase
      .from('usage_tracking')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'active')
      .order('start_time', { ascending: false });

    if (error) throw error;

    return (data || []).map(session => ({
      sessionId: session.session_id,
      assistantId: session.assistant_id,
      userId: session.user_id,
      communicationMedium: session.communication_medium,
      provider: session.provider,
      region: session.region,
      startTime: new Date(session.start_time),
      endTime: session.end_time ? new Date(session.end_time) : undefined,
      durationMinutes: session.duration_minutes,
      totalCost: session.total_cost,
      status: session.status,
      metadata: session.metadata
    }));
  } catch (error) {
    console.error('Error getting active usage sessions:', error);
    return [];
  }
}

/**
 * Check if user has sufficient balance for a session
 */
export async function checkSufficientBalance(
  userId: string,
  estimatedMinutes: number,
  communicationMedium: string = 'webrtc',
  region: string = 'GH'
): Promise<{ sufficient: boolean; balance: number; estimatedCost: number }> {
  try {
    const balance = await getWalletBalance(userId);
    const pricing = await getPricingForRegion(region, communicationMedium);
    const estimatedCost = estimatedMinutes * pricing.finalCostPerMinute;

    return {
      sufficient: balance >= estimatedCost,
      balance,
      estimatedCost
    };
  } catch (error) {
    console.error('Error checking sufficient balance:', error);
    return {
      sufficient: false,
      balance: 0,
      estimatedCost: 0
    };
  }
}

/**
 * Get user's usage alerts
 */
export async function getUserAlerts(userId: string): Promise<{
  id: string;
  alertType: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}[]> {
  try {
    const { data, error } = await supabase
      .from('usage_alerts')
      .select('*')
      .eq('user_id', userId)
      .eq('is_resolved', false)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  } catch (error) {
    console.error('Error getting user alerts:', error);
    return [];
  }
}

/**
 * Mark alert as read
 */
export async function markAlertAsRead(alertId: string): Promise<void> {
  try {
    const { error } = await supabase
      .from('usage_alerts')
      .update({ is_read: true })
      .eq('id', alertId);

    if (error) throw error;
  } catch (error) {
    console.error('Error marking alert as read:', error);
    throw error;
  }
}

/**
 * Get regional pricing bundles for user
 */
export async function getRegionalBundles(userId: string): Promise<{
  id: string;
  name: string;
  description: string;
  price: number;
  minutes: number;
  communicationMedium: string;
  currency: string;
}[]> {
  try {
    const { data, error } = await supabase
      .rpc('get_user_regional_bundles', { p_user_id: userId });

    if (error) throw error;

    return (data || []).map(bundle => ({
      id: bundle.id,
      name: bundle.name,
      description: bundle.description,
      price: bundle.price,
      minutes: bundle.minutes,
      communicationMedium: bundle.communication_medium,
      currency: bundle.currency
    }));
  } catch (error) {
    console.error('Error getting regional bundles:', error);
    return [];
  }
}

/**
 * Estimate cost for a session
 */
export async function estimateSessionCost(
  estimatedMinutes: number,
  communicationMedium: string = 'webrtc',
  region: string = 'GH'
): Promise<{
  baseCost: number;
  markup: number;
  finalCost: number;
  currency: string;
}> {
  try {
    const pricing = await getPricingForRegion(region, communicationMedium);
    
    return {
      baseCost: estimatedMinutes * pricing.baseCostPerMinute,
      markup: estimatedMinutes * pricing.baseCostPerMinute * (pricing.markupPercentage / 100),
      finalCost: estimatedMinutes * pricing.finalCostPerMinute,
      currency: pricing.currency
    };
  } catch (error) {
    console.error('Error estimating session cost:', error);
    return {
      baseCost: 0,
      markup: 0,
      finalCost: 0,
      currency: 'USD'
    };
  }
}
