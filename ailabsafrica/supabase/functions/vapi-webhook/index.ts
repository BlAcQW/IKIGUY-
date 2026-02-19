import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface VapiWebhookEvent {
  message: {
    type: string;
    call?: {
      id: string;
      assistantId: string;
      status: string;
      startTime: string;
      endTime?: string;
      duration?: number;
      cost?: number;
    };
    artifact?: {
      transcript?: string;
      recording?: {
        url?: string;
      };
    };
    endedReason?: string;
  };
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Verify webhook signature (optional but recommended)
    const signature = req.headers.get('x-vapi-signature');
    if (!signature) {
      console.warn('No Vapi signature found in webhook request');
    }

    const body: VapiWebhookEvent = await req.json();
    console.log('Received Vapi webhook:', body);

    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    // Handle different webhook event types
    switch (body.message.type) {
      case 'call-start':
        await handleCallStart(supabaseClient, body);
        break;
      
      case 'call-end':
        await handleCallEnd(supabaseClient, body);
        break;
      
      case 'end-of-call-report':
        await handleEndOfCallReport(supabaseClient, body);
        break;
      
      case 'transcript':
        await handleTranscript(supabaseClient, body);
        break;
      
      default:
        console.log(`Unhandled webhook event type: ${body.message.type}`);
    }

    return new Response(
      JSON.stringify({ success: true }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Error processing webhook:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});

async function handleCallStart(supabase: any, event: VapiWebhookEvent) {
  if (!event.message.call) return;

  const { call } = event.message;
  
  // Insert or update call record
  const { error } = await supabase
    .from('usage_tracking')
    .upsert({
      vapi_call_id: call.id,
      assistant_id: call.assistantId,
      status: call.status,
      start_time: call.startTime,
      communication_medium: 'phone', // Default, can be updated later
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }, {
      onConflict: 'vapi_call_id'
    });

  if (error) {
    console.error('Error handling call start:', error);
  }
}

async function handleCallEnd(supabase: any, event: VapiWebhookEvent) {
  if (!event.message.call) return;

  const { call } = event.message;
  
  // Update call record with end time and duration
  const { error } = await supabase
    .from('usage_tracking')
    .update({
      status: call.status,
      end_time: call.endTime,
      duration_minutes: call.duration,
      total_cost: call.cost,
      updated_at: new Date().toISOString()
    })
    .eq('vapi_call_id', call.id);

  if (error) {
    console.error('Error handling call end:', error);
  }
}

async function handleEndOfCallReport(supabase: any, event: VapiWebhookEvent) {
  if (!event.message.call || !event.message.artifact) return;

  const { call, artifact } = event.message;
  
  // Update call record with transcript and final details
  const updateData: any = {
    status: call.status,
    end_time: call.endTime,
    duration_minutes: call.duration,
    total_cost: call.cost,
    transcript: artifact.transcript,
    ended_reason: event.message.endedReason,
    updated_at: new Date().toISOString()
  };

  // Add recording URL if available
  if (artifact.recording?.url) {
    updateData.recording_url = artifact.recording.url;
  }

  const { error } = await supabase
    .from('usage_tracking')
    .update(updateData)
    .eq('vapi_call_id', call.id);

  if (error) {
    console.error('Error handling end-of-call report:', error);
  }
}

async function handleTranscript(supabase: any, event: VapiWebhookEvent) {
  if (!event.message.call || !event.message.artifact?.transcript) return;

  const { call, artifact } = event.message;
  
  // Update call record with transcript
  const { error } = await supabase
    .from('usage_tracking')
    .update({
      transcript: artifact.transcript,
      updated_at: new Date().toISOString()
    })
    .eq('vapi_call_id', call.id);

  if (error) {
    console.error('Error handling transcript:', error);
  }
}
