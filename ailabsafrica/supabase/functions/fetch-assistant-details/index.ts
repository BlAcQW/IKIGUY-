import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface AssistantDetails {
	id: string;
	name: string;
	description?: string;
	model: string;
	voice: string;
	firstMessage?: string;
	systemPrompt?: string;
	createdAt: string;
	updatedAt: string;
	status: string;
	phoneNumberId?: string;
	phoneNumber?: string;
	serverUrl?: string;
	clientMessages?: string[];
	metadata?: Record<string, any>;
}

async function fetchAssistantFromVapi(assistantId: string): Promise<AssistantDetails | null> {
	const vapiToken = Deno.env.get("VAPI_PRIVATE_KEY");
	if (!vapiToken) {
		throw new Error("Missing VAPI_PRIVATE_KEY environment variable");
	}

	const url = `https://api.vapi.ai/assistant/${assistantId}`;
	console.log("[fetch-assistant-details] Fetching assistant from:", url);

	try {
		const response = await fetch(url, {
			method: "GET",
			headers: {
				"Authorization": `Bearer ${vapiToken}`,
				"Content-Type": "application/json",
			},
		});

		console.log("[fetch-assistant-details] Vapi API response status:", response.status);

		if (!response.ok) {
			const errorText = await response.text();
			console.error("[fetch-assistant-details] Vapi API error:", response.status, errorText);
			
			if (response.status === 404) {
				throw new Error(`Assistant not found: ${assistantId}. Please check the assistant ID.`);
			} else if (response.status === 401) {
				throw new Error("Invalid Vapi API key. Please check your VAPI_PRIVATE_KEY configuration.");
			} else {
				throw new Error(`Vapi API error (${response.status}): ${errorText}`);
			}
		}

		const data = await response.json();
		console.log("[fetch-assistant-details] Received assistant data for:", assistantId);

		// Transform the data to our format
		const assistantDetails: AssistantDetails = {
			id: data.id,
			name: data.name || 'Unnamed Assistant',
			description: data.description,
			model: data.model?.provider ? `${data.model.provider}/${data.model.name}` : 'Unknown',
			voice: data.voice?.provider && data.voice?.name ? `${data.voice.provider}/${data.voice.name}` : 'Unknown',
			firstMessage: data.firstMessage,
			systemPrompt: data.systemPrompt,
			createdAt: data.createdAt,
			updatedAt: data.updatedAt,
			status: data.status || 'active',
			phoneNumberId: data.phoneNumberId,
			phoneNumber: data.phoneNumber,
			serverUrl: data.serverUrl,
			clientMessages: data.clientMessages,
			metadata: data.metadata,
		};

		return assistantDetails;
	} catch (error) {
		console.error("[fetch-assistant-details] Error fetching from Vapi:", error);
		throw error;
	}
}

async function saveAssistantToDatabase(assistantDetails: AssistantDetails, userId: string, customUrl?: string) {
	const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
	const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

	const supabase = createClient(supabaseUrl, supabaseServiceKey);

	try {
		// Check if assistant already exists for this user
		const { data: existingAssistant, error: checkError } = await supabase
			.from('custom_demos')
			.select('id')
			.eq('assistant_id', assistantDetails.id)
			.eq('user_id', userId)
			.single();

		// If assistant exists for this user, return early
		if (existingAssistant) {
			console.log("[fetch-assistant-details] Assistant already exists for this user:", assistantDetails.id);
			return { success: true, message: "Assistant already exists in your dashboard" };
		}

		// If error is not "not found", something else went wrong
		if (checkError && checkError.code !== 'PGRST116') {
			console.error("[fetch-assistant-details] Error checking existing assistant:", checkError);
			throw new Error(`Database check error: ${checkError.message}`);
		}

		// Insert new assistant
		const { data, error } = await supabase
			.from('custom_demos')
			.insert({
				user_id: userId,
				assistant_id: assistantDetails.id,
				assistant_name: assistantDetails.name,
				description: assistantDetails.description || '',
				assistant_type: 'external', // Mark as external assistant
				voice_id: assistantDetails.voice,
				model: assistantDetails.model,
				system_prompt: assistantDetails.systemPrompt || '',
				first_message: assistantDetails.firstMessage || '',
				website_url: customUrl || '', // Use custom URL if provided
				demo_url: customUrl || '', // Use custom URL for demo preview
				status: 'active', // Add status field for consistency
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString(),
				metadata: assistantDetails.metadata || {},
			})
			.select()
			.single();

		if (error) {
			console.error("[fetch-assistant-details] Error saving assistant to database:", error);
			if (error.code === '23505') { // Unique constraint violation
				throw new Error("Assistant already exists in your dashboard");
			}
			throw new Error(`Database error: ${error.message}`);
		}

		console.log("[fetch-assistant-details] Assistant saved to database:", data.id);
		return { success: true, message: "Assistant imported successfully", data };

	} catch (error) {
		console.error("[fetch-assistant-details] Failed to save assistant to database:", error);
		throw error;
	}
}

serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response(null, { headers: corsHeaders });
	}

	try {
		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;

		const supabaseAuth = createClient(supabaseUrl, supabaseAnonKey, {
			global: { headers: { Authorization: req.headers.get("Authorization") || "" } },
		});

		const {
			data: { user },
		} = await supabaseAuth.auth.getUser();

		if (!user) {
			return new Response(JSON.stringify({ error: "Unauthorized" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		const requestData = await req.json();
		const { assistantId, customUrl } = requestData;

		if (!assistantId) {
			return new Response(JSON.stringify({ error: "Assistant ID is required" }), {
				status: 400,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		console.log("[fetch-assistant-details] Request:", { assistantId, user: user.id });

		// Fetch assistant from Vapi
		const assistantDetails = await fetchAssistantFromVapi(assistantId);

		if (!assistantDetails) {
			return new Response(JSON.stringify({ error: "Assistant not found" }), {
				status: 404,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		// Save to database
		const saveResult = await saveAssistantToDatabase(assistantDetails, user.id, customUrl);

		console.log("[fetch-assistant-details] Assistant details fetched:", {
			id: assistantDetails.id,
			name: assistantDetails.name,
			model: assistantDetails.model,
			voice: assistantDetails.voice,
		});

		return new Response(JSON.stringify({
			assistant: assistantDetails,
			import: saveResult,
		}), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	} catch (error: any) {
		console.error("[fetch-assistant-details] Error:", error);
		return new Response(JSON.stringify({ error: error.message || "Internal error" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
