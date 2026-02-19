import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    // Get the current user
    const { data: { user }, error: userError } = await supabaseClient.auth.getUser()
    if (userError || !user) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { action, ...params } = await req.json()

    switch (action) {
      case 'create_referral_link':
        return await handleCreateReferralLink(supabaseClient, user.id, params)
      case 'get_user_referrals':
        return await handleGetUserReferrals(supabaseClient, user.id, params)
      case 'get_referral_stats':
        return await handleGetReferralStats(supabaseClient, user.id, params)
      case 'track_referral_conversion':
        return await handleTrackReferralConversion(supabaseClient, params)
      case 'get_referral_rewards':
        return await handleGetReferralRewards(supabaseClient, user.id, params)
      case 'create_lead_campaign':
        return await handleCreateLeadCampaign(supabaseClient, user.id, params)
      case 'get_lead_campaigns':
        return await handleGetLeadCampaigns(supabaseClient, user.id, params)
      case 'update_lead_campaign':
        return await handleUpdateLeadCampaign(supabaseClient, user.id, params)
      case 'delete_lead_campaign':
        return await handleDeleteLeadCampaign(supabaseClient, user.id, params)
      case 'create_lead_source':
        return await handleCreateLeadSource(supabaseClient, user.id, params)
      case 'get_lead_sources':
        return await handleGetLeadSources(supabaseClient, user.id, params)
      case 'create_lead_contact':
        return await handleCreateLeadContact(supabaseClient, user.id, params)
      case 'get_lead_contacts':
        return await handleGetLeadContacts(supabaseClient, user.id, params)
      case 'update_lead_contact':
        return await handleUpdateLeadContact(supabaseClient, user.id, params)
      case 'create_lead_activity':
        return await handleCreateLeadActivity(supabaseClient, user.id, params)
      case 'get_lead_activities':
        return await handleGetLeadActivities(supabaseClient, user.id, params)
      case 'get_campaign_analytics':
        return await handleGetCampaignAnalytics(supabaseClient, user.id, params)
      case 'get_referral_programs':
        return await handleGetReferralPrograms(supabaseClient, params)
      default:
        return new Response(
          JSON.stringify({ error: 'Invalid action' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    }
  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// Referral Management Functions
async function handleCreateReferralLink(supabaseClient: any, userId: string, params: any) {
  try {
    const { programId = null } = params

    // Get default program if none specified
    let programIdToUse = programId
    if (!programIdToUse) {
      const { data: programs } = await supabaseClient
        .from('referral_programs')
        .select('id')
        .eq('is_active', true)
        .limit(1)
      
      if (programs && programs.length > 0) {
        programIdToUse = programs[0].id
      } else {
        return new Response(
          JSON.stringify({ error: 'No active referral program found' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }
    }

    // Generate referral code using the database function
    const { data: referralCode, error: codeError } = await supabaseClient
      .rpc('generate_referral_code')

    if (codeError) {
      throw codeError
    }

    // Create referral link
    const baseUrl = Deno.env.get('FRONTEND_URL') || 'http://localhost:3000'
    const referralLink = `${baseUrl}/signup?ref=${referralCode}`

    // Insert referral record
    const { data: referral, error } = await supabaseClient
      .from('user_referrals')
      .insert({
        referrer_id: userId,
        referral_code: referralCode,
        referral_link: referralLink,
        program_id: programIdToUse,
        utm_source: params.utmSource,
        utm_medium: params.utmMedium,
        utm_campaign: params.utmCampaign
      })
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: referral }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error creating referral link:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create referral link' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetUserReferrals(supabaseClient: any, userId: string, params: any) {
  try {
    const { status, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('user_referrals')
      .select(`
        *,
        referral_programs(name, description, reward_type, reward_value),
        referred_user:referred_id(email)
      `)
      .eq('referrer_id', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    const { data: referrals, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: referrals }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting user referrals:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get referrals' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetReferralStats(supabaseClient: any, userId: string, params: any) {
  try {
    const { data: stats, error } = await supabaseClient
      .rpc('get_user_referral_stats', { user_uuid: userId })

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: stats }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting referral stats:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get referral stats' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleTrackReferralConversion(supabaseClient: any, params: any) {
  try {
    const { referralCode, newUserId } = params

    if (!referralCode || !newUserId) {
      return new Response(
        JSON.stringify({ error: 'Referral code and new user ID are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: success, error } = await supabaseClient
      .rpc('track_referral_conversion', {
        referral_code_param: referralCode,
        new_user_id: newUserId
      })

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: { converted: success } }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error tracking referral conversion:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to track referral conversion' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetReferralRewards(supabaseClient: any, userId: string, params: any) {
  try {
    const { status, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('referral_rewards')
      .select(`
        *,
        referral_programs(name, description),
        user_referrals(referral_code, referred_user:referred_id(email))
      `)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    const { data: rewards, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: rewards }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting referral rewards:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get referral rewards' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

// Lead Campaign Management Functions
async function handleCreateLeadCampaign(supabaseClient: any, userId: string, params: any) {
  try {
    const { name, description, campaignType, budget, targetAudience, settings } = params

    if (!name || !campaignType) {
      return new Response(
        JSON.stringify({ error: 'Name and campaign type are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: campaign, error } = await supabaseClient
      .from('lead_campaigns')
      .insert({
        name,
        description,
        campaign_type: campaignType,
        budget,
        target_audience: targetAudience || {},
        settings: settings || {},
        created_by: userId
      })
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: campaign }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error creating lead campaign:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create lead campaign' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetLeadCampaigns(supabaseClient: any, userId: string, params: any) {
  try {
    const { status, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('lead_campaigns')
      .select('*')
      .eq('created_by', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    const { data: campaigns, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: campaigns }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting lead campaigns:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get lead campaigns' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleUpdateLeadCampaign(supabaseClient: any, userId: string, params: any) {
  try {
    const { id, ...updateData } = params

    if (!id) {
      return new Response(
        JSON.stringify({ error: 'Campaign ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: campaign, error } = await supabaseClient
      .from('lead_campaigns')
      .update(updateData)
      .eq('id', id)
      .eq('created_by', userId)
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: campaign }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error updating lead campaign:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to update lead campaign' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleDeleteLeadCampaign(supabaseClient: any, userId: string, params: any) {
  try {
    const { id } = params

    if (!id) {
      return new Response(
        JSON.stringify({ error: 'Campaign ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { error } = await supabaseClient
      .from('lead_campaigns')
      .delete()
      .eq('id', id)
      .eq('created_by', userId)

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error deleting lead campaign:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to delete lead campaign' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

// Lead Source Management Functions
async function handleCreateLeadSource(supabaseClient: any, userId: string, params: any) {
  try {
    const { name, sourceType, campaignId, utmSource, utmMedium, utmCampaign, utmTerm, utmContent, costPerLead } = params

    if (!name || !sourceType) {
      return new Response(
        JSON.stringify({ error: 'Name and source type are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: source, error } = await supabaseClient
      .from('lead_sources')
      .insert({
        name,
        source_type: sourceType,
        campaign_id: campaignId,
        utm_source: utmSource,
        utm_medium: utmMedium,
        utm_campaign: utmCampaign,
        utm_term: utmTerm,
        utm_content: utmContent,
        cost_per_lead: costPerLead
      })
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: source }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error creating lead source:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create lead source' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetLeadSources(supabaseClient: any, userId: string, params: any) {
  try {
    const { campaignId, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('lead_sources')
      .select(`
        *,
        lead_campaigns(name, campaign_type)
      `)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (campaignId) {
      query = query.eq('campaign_id', campaignId)
    }

    const { data: sources, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: sources }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting lead sources:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get lead sources' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

// Lead Contact Management Functions
async function handleCreateLeadContact(supabaseClient: any, userId: string, params: any) {
  try {
    const { email, firstName, lastName, phone, company, jobTitle, sourceId, campaignId, tags, notes } = params

    if (!email || !sourceId) {
      return new Response(
        JSON.stringify({ error: 'Email and source ID are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: contact, error } = await supabaseClient
      .from('lead_contacts')
      .insert({
        email,
        first_name: firstName,
        last_name: lastName,
        phone,
        company,
        job_title: jobTitle,
        source_id: sourceId,
        campaign_id: campaignId,
        tags,
        notes,
        assigned_to: userId
      })
      .select()
      .single()

    if (error) throw error

    // Calculate lead score
    const { data: score } = await supabaseClient
      .rpc('calculate_lead_score', { lead_uuid: contact.id })

    if (score) {
      await supabaseClient
        .from('lead_contacts')
        .update({ lead_score: score })
        .eq('id', contact.id)
    }

    return new Response(
      JSON.stringify({ success: true, data: contact }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error creating lead contact:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create lead contact' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetLeadContacts(supabaseClient: any, userId: string, params: any) {
  try {
    const { status, campaignId, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('lead_contacts')
      .select(`
        *,
        lead_sources(name, source_type),
        lead_campaigns(name, campaign_type),
        assigned_user:assigned_to(email)
      `)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (status) {
      query = query.eq('status', status)
    }

    if (campaignId) {
      query = query.eq('campaign_id', campaignId)
    }

    const { data: contacts, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: contacts }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting lead contacts:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get lead contacts' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleUpdateLeadContact(supabaseClient: any, userId: string, params: any) {
  try {
    const { id, ...updateData } = params

    if (!id) {
      return new Response(
        JSON.stringify({ error: 'Contact ID is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: contact, error } = await supabaseClient
      .from('lead_contacts')
      .update(updateData)
      .eq('id', id)
      .eq('assigned_to', userId)
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: contact }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error updating lead contact:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to update lead contact' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

// Lead Activity Management Functions
async function handleCreateLeadActivity(supabaseClient: any, userId: string, params: any) {
  try {
    const { leadId, activityType, subject, description, durationMinutes, outcome, nextAction } = params

    if (!leadId || !activityType) {
      return new Response(
        JSON.stringify({ error: 'Lead ID and activity type are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: activity, error } = await supabaseClient
      .from('lead_activities')
      .insert({
        lead_id: leadId,
        activity_type: activityType,
        subject,
        description,
        performed_by: userId,
        duration_minutes: durationMinutes,
        outcome,
        next_action: nextAction
      })
      .select()
      .single()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: activity }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error creating lead activity:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create lead activity' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetLeadActivities(supabaseClient: any, userId: string, params: any) {
  try {
    const { leadId, limit = 50, offset = 0 } = params

    let query = supabaseClient
      .from('lead_activities')
      .select(`
        *,
        lead_contacts(email, first_name, last_name),
        performed_user:performed_by(email)
      `)
      .order('activity_date', { ascending: false })
      .range(offset, offset + limit - 1)

    if (leadId) {
      query = query.eq('lead_id', leadId)
    }

    const { data: activities, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: activities }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting lead activities:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get lead activities' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

// Analytics Functions
async function handleGetCampaignAnalytics(supabaseClient: any, userId: string, params: any) {
  try {
    const { campaignId, startDate, endDate, metricType } = params

    let query = supabaseClient
      .from('marketing_analytics')
      .select('*')
      .order('date', { ascending: true })

    if (campaignId) {
      query = query.eq('campaign_id', campaignId)
    }

    if (startDate) {
      query = query.gte('date', startDate)
    }

    if (endDate) {
      query = query.lte('date', endDate)
    }

    if (metricType) {
      query = query.eq('metric_type', metricType)
    }

    const { data: analytics, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: analytics }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting campaign analytics:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get campaign analytics' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleGetReferralPrograms(supabaseClient: any, params: any) {
  try {
    const { isActive = true } = params

    let query = supabaseClient
      .from('referral_programs')
      .select('*')
      .order('created_at', { ascending: false })

    if (isActive !== undefined) {
      query = query.eq('is_active', isActive)
    }

    const { data: programs, error } = await query

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data: programs }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Error getting referral programs:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to get referral programs' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}
