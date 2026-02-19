import { serve } from "https://deno.land/std@0.190.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Attempt to fetch from Vapi API, fallback to static list
    const VAPI_URL = "https://api.vapi.ai/voices";
    const token = Deno.env.get("VAPI_PRIVATE_KEY");
    let voices: Array<{ id: string; name: string }>; 

    try {
      if (!token) throw new Error("Missing VAPI_PRIVATE_KEY");
      const res = await fetch(VAPI_URL, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      voices = (json?.items || json?.voices || json || [])
        .map((v: any) => ({ id: v.id || v.voiceId || v.name, name: v.name || v.id || v.voiceId }))
        .filter((v: any) => v.id && v.name);
      if (!Array.isArray(voices) || voices.length === 0) throw new Error("Empty voices");
    } catch (_e) {
      // Fallback curated list - using only valid Vapi voice IDs
      voices = [
        { id: "Paige", name: "Paige" },
        { id: "Elliot", name: "Elliot" },
        { id: "Kylie", name: "Kylie" },
        { id: "Rohan", name: "Rohan" },
        { id: "Lily", name: "Lily" },
        { id: "Savannah", name: "Savannah" },
        { id: "Hana", name: "Hana" },
        { id: "Neha", name: "Neha" },
        { id: "Cole", name: "Cole" },
        { id: "Harry", name: "Harry" },
        { id: "Spencer", name: "Spencer" },
      ];
    }

    return new Response(JSON.stringify({ voices }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error: any) {
    console.error("list-vapi-voices error:", error);
    return new Response(JSON.stringify({ error: error.message || "Internal error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
