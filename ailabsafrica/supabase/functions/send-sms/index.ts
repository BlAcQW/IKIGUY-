import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface SendSMSRequest {
  phone_number: string;
  message: string;
  user_id?: string;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Create Supabase client
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Parse request body
    const { phone_number, message, user_id }: SendSMSRequest = await req.json();

    // Validate required fields
    if (!phone_number || !message) {
      return new Response(
        JSON.stringify({ 
          error: "Missing required fields: phone_number and message are required" 
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        }
      );
    }

    // Validate phone number format (basic validation)
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    if (!phoneRegex.test(phone_number.replace(/\s/g, ''))) {
      return new Response(
        JSON.stringify({ 
          error: "Invalid phone number format. Please use international format (e.g., +1234567890)" 
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        }
      );
    }

    // Validate message length (SMS limit is typically 160 characters)
    if (message.length > 160) {
      return new Response(
        JSON.stringify({ 
          error: "Message too long. SMS messages must be 160 characters or less" 
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        }
      );
    }

    console.log(`[send-sms] Sending SMS to ${phone_number}: ${message}`);

    // Send SMS using Supabase's built-in SMS functionality
    const { data, error } = await supabase.auth.admin.sendRawSMS({
      phone: phone_number,
      message: message,
    });

    if (error) {
      console.error("[send-sms] SMS sending error:", error);
      return new Response(
        JSON.stringify({ 
          error: `Failed to send SMS: ${error.message}` 
        }),
        {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        }
      );
    }

    console.log("[send-sms] SMS sent successfully:", data);

    // Log the SMS action if user_id is provided
    if (user_id) {
      try {
        await supabase
          .from('assistant_actions')
          .insert([{
            user_id: user_id,
            action: 'send_sms',
            details: JSON.stringify({
              phone_number: phone_number,
              message: message,
              timestamp: new Date().toISOString()
            }),
            created_at: new Date().toISOString()
          }]);
      } catch (logError) {
        console.error("[send-sms] Failed to log SMS action:", logError);
        // Don't fail the request if logging fails
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: "SMS sent successfully",
        data: {
          phone_number: phone_number,
          message_length: message.length,
          timestamp: new Date().toISOString()
        }
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      }
    );

  } catch (error) {
    console.error("[send-sms] Error:", error);
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : "Internal server error" 
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      }
    );
  }
});
