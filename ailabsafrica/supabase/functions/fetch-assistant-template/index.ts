import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface FetchTemplateRequest {
  templateId: string;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { templateId }: FetchTemplateRequest = await req.json();

    if (!templateId) {
      return new Response(JSON.stringify({ error: "Template ID is required" }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const token = Deno.env.get("VAPI_PRIVATE_KEY");
    if (!token) {
      throw new Error("Missing VAPI_PRIVATE_KEY");
    }

    console.log("[fetch-assistant-template] Fetching template:", templateId);

    // Fetch the assistant template from Vapi
    const response = await fetch(`https://api.vapi.ai/assistant/${templateId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[fetch-assistant-template] Vapi error:", response.status, errorText);
      throw new Error(`Failed to fetch template: ${response.status} - ${errorText}`);
    }

    const template = await response.json();
    console.log("[fetch-assistant-template] Template fetched successfully:", {
      id: template.id,
      name: template.name,
      hasModel: !!template.model,
      hasVoice: !!template.voice
    });

    return new Response(JSON.stringify({
      success: true,
      template: {
        id: template.id,
        name: template.name,
        systemPrompt: template.model?.messages?.[0]?.content || "",
        firstMessage: template.firstMessage || "",
        voice: template.voice,
        model: template.model
      }
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('[fetch-assistant-template] Error:', error);
    return new Response(JSON.stringify({ 
      error: error.message,
      success: false 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
