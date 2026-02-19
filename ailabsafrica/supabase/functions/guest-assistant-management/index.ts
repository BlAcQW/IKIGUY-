import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface GuestAssistantPayload {
  assistant_name: string;
  assistant_type: string;
  assistant_id: string;
  voice_id?: string;
  voice_name?: string;
  description?: string;
  website_url?: string;
  demo_url: string;
  guest_email?: string;
  guest_password: string;
}

interface GuestLoginPayload {
  guest_email: string;
  guest_password: string;
}

// Fallback password hashing function
async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { action, ...payload } = await req.json()

    switch (action) {
      case 'create':
        return await handleCreateAssistant(supabase, payload as GuestAssistantPayload)
      
      case 'login':
        return await handleGuestLogin(supabase, payload as GuestLoginPayload)
      
      case 'list':
        return await handleListAssistants(supabase, payload as GuestLoginPayload)
      
      default:
        return new Response(
          JSON.stringify({ error: 'Invalid action' }),
          {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        )
    }
  } catch (error) {
    console.error('Error in guest assistant management:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

async function handleCreateAssistant(supabase: any, payload: GuestAssistantPayload) {
  const { guest_password, guest_email, ...assistantData } = payload

  // Try to hash the password using the database function first
  let hashedPassword: string;
  try {
    const { data: hashData, error: hashError } = await supabase
      .rpc('hash_guest_password', { password: guest_password })

    if (hashError) {
      console.warn('Database hash function failed, using fallback:', hashError)
      // Fallback to client-side hashing
      hashedPassword = await hashPassword(guest_password)
    } else {
      hashedPassword = hashData
    }
  } catch (error) {
    console.warn('Password hashing error, using fallback:', error)
    // Fallback to client-side hashing
    hashedPassword = await hashPassword(guest_password)
  }

  // Create the assistant record
  const { data, error } = await supabase
    .from('custom_demos')
    .insert({
      ...assistantData,
      user_id: null, // Guest users don't have a user_id
      is_guest: true,
      guest_password_hash: hashedPassword,
      guest_email: guest_email || null,
      status: 'created'
    })
    .select()

  if (error) {
    console.error('Error creating assistant:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to create assistant' }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  return new Response(
    JSON.stringify({ 
      success: true, 
      data: data[0],
      message: 'Assistant created successfully'
    }),
    {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handleGuestLogin(supabase: any, payload: GuestLoginPayload) {
  const { guest_email, guest_password } = payload

  // Hash the password for comparison
  let hashedPassword: string;
  try {
    const { data: hashData, error: hashError } = await supabase
      .rpc('hash_guest_password', { password: guest_password })

    if (hashError) {
      console.warn('Database hash function failed, using fallback:', hashError)
      hashedPassword = await hashPassword(guest_password)
    } else {
      hashedPassword = hashData
    }
  } catch (error) {
    console.warn('Password hashing error, using fallback:', error)
    hashedPassword = await hashPassword(guest_password)
  }

  // Find the assistant by email and password hash
  const { data, error } = await supabase
    .from('custom_demos')
    .select('*')
    .eq('guest_email', guest_email)
    .eq('guest_password_hash', hashedPassword)
    .eq('is_guest', true)
    .single()

  if (error || !data) {
    return new Response(
      JSON.stringify({ error: 'Invalid credentials' }),
      {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  return new Response(
    JSON.stringify({ 
      success: true, 
      data,
      message: 'Login successful'
    }),
    {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}

async function handleListAssistants(supabase: any, payload: GuestLoginPayload) {
  const { guest_email, guest_password } = payload

  // Hash the password for comparison
  let hashedPassword: string;
  try {
    const { data: hashData, error: hashError } = await supabase
      .rpc('hash_guest_password', { password: guest_password })

    if (hashError) {
      console.warn('Database hash function failed, using fallback:', hashError)
      hashedPassword = await hashPassword(guest_password)
    } else {
      hashedPassword = hashData
    }
  } catch (error) {
    console.warn('Password hashing error, using fallback:', error)
    hashedPassword = await hashPassword(guest_password)
  }

  // Get all assistants for this guest user
  const { data, error } = await supabase
    .from('custom_demos')
    .select('*')
    .eq('guest_email', guest_email)
    .eq('guest_password_hash', hashedPassword)
    .eq('is_guest', true)
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error listing assistants:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to list assistants' }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }

  return new Response(
    JSON.stringify({ 
      success: true, 
      data: data || [],
      message: 'Assistants retrieved successfully'
    }),
    {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
}
