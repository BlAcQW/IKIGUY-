import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface CallData {
	id: string;
	assistantId: string;
	assistantName?: string;
	status: string;
	duration: number; // in seconds
	cost: number; // in USD
	startTime: string;
	endTime: string;
	transcript?: string;
	summary?: string;
	metadata?: Record<string, any>;
	phoneNumber?: string;
	callType: 'inbound' | 'outbound' | 'web';
	createdAt: string;
	updatedAt: string;
}

interface AnalyticsResponse {
	calls: CallData[];
	totalMinutes: number;
	totalCost: number;
	callCount: number;
	assistantBreakdown: {
		assistantId: string;
		assistantName: string;
		callCount: number;
		totalMinutes: number;
		totalCost: number;
		avgDuration: number;
	}[];
	timeRange: {
		start: string;
		end: string;
	};
}

async function fetchVapiCalls(assistantId?: string, startDate?: string, endDate?: string): Promise<CallData[]> {
	const vapiToken = Deno.env.get("VAPI_PRIVATE_KEY");
	if (!vapiToken) {
		throw new Error("Missing VAPI_PRIVATE_KEY");
	}

	// Build query parameters
	const params = new URLSearchParams();
	if (assistantId) {
		params.append("assistantId", assistantId);
	}
	if (startDate) {
		params.append("createdAtGe", startDate);
	}
	if (endDate) {
		params.append("createdAtLe", endDate);
	}
	params.append("limit", "100"); // Get up to 100 calls

	const url = `https://api.vapi.ai/call?${params.toString()}`;
	console.log("[fetch-call-analytics] Fetching calls from:", url);

	const response = await fetch(url, {
		method: "GET",
		headers: {
			"Authorization": `Bearer ${vapiToken}`,
			"Content-Type": "application/json",
		},
	});

	if (!response.ok) {
		const errorText = await response.text();
		console.error("[fetch-call-analytics] Vapi API error:", response.status, errorText);
		throw new Error(`Vapi API error: ${response.status} - ${errorText}`);
	}

	const data = await response.json();
	console.log("[fetch-call-analytics] Received calls:", data.length || 0);

	// Transform the data to our format
	const calls: CallData[] = [];
	for (const call of data) {
		// Calculate duration in seconds
		const startTime = new Date(call.createdAt);
		const endTime = call.endedAt ? new Date(call.endedAt) : new Date();
		const duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000);

		// Calculate cost (Vapi charges $0.05 per minute after 1000 free minutes)
		// This is a simplified calculation - actual costs may vary
		const minutes = duration / 60;
		const cost = minutes * 0.05; // $0.05 per minute

		const callData: CallData = {
			id: call.id,
			assistantId: call.assistantId,
			status: call.status || 'unknown',
			duration,
			cost,
			startTime: call.createdAt,
			endTime: call.endedAt || new Date().toISOString(),
			transcript: call.transcript,
			summary: call.summary,
			metadata: call.metadata,
			phoneNumber: call.phoneNumber,
			callType: call.type || 'web',
			createdAt: call.createdAt,
			updatedAt: call.updatedAt,
		};

		calls.push(callData);
	}

	return calls;
}

async function getAssistantNames(calls: CallData[]): Promise<Map<string, string>> {
	const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
	const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
	
	const supabase = createClient(supabaseUrl, supabaseServiceKey);
	
	const assistantIds = [...new Set(calls.map(call => call.assistantId))];
	const assistantNames = new Map<string, string>();

	if (assistantIds.length === 0) return assistantNames;

	try {
		// Get assistant names from our database
		const { data, error } = await supabase
			.from('custom_demos')
			.select('assistant_id, assistant_name')
			.in('assistant_id', assistantIds);

		if (error) {
			console.warn("[fetch-call-analytics] Error fetching assistant names:", error);
		} else if (data) {
			for (const assistant of data) {
				assistantNames.set(assistant.assistant_id, assistant.assistant_name);
			}
		}
	} catch (error) {
		console.warn("[fetch-call-analytics] Failed to fetch assistant names:", error);
	}

	return assistantNames;
}

function calculateAnalytics(calls: CallData[], assistantNames: Map<string, string>): AnalyticsResponse {
	// Calculate totals
	const totalMinutes = calls.reduce((sum, call) => sum + (call.duration / 60), 0);
	const totalCost = calls.reduce((sum, call) => sum + call.cost, 0);
	const callCount = calls.length;

	// Group by assistant
	const assistantMap = new Map<string, {
		assistantId: string;
		assistantName: string;
		callCount: number;
		totalMinutes: number;
		totalCost: number;
		durations: number[];
	}>();

	for (const call of calls) {
		const assistantId = call.assistantId;
		const assistantName = assistantNames.get(assistantId) || `Assistant ${assistantId.slice(0, 8)}`;
		
		if (!assistantMap.has(assistantId)) {
			assistantMap.set(assistantId, {
				assistantId,
				assistantName,
				callCount: 0,
				totalMinutes: 0,
				totalCost: 0,
				durations: [],
			});
		}

		const assistant = assistantMap.get(assistantId)!;
		assistant.callCount++;
		assistant.totalMinutes += call.duration / 60;
		assistant.totalCost += call.cost;
		assistant.durations.push(call.duration);
	}

	// Convert to array and calculate averages
	const assistantBreakdown = Array.from(assistantMap.values()).map(assistant => ({
		...assistant,
		avgDuration: assistant.durations.length > 0 
			? assistant.durations.reduce((sum, dur) => sum + dur, 0) / assistant.durations.length 
			: 0,
		durations: undefined, // Remove from output
	}));

	// Sort by total cost (descending)
	assistantBreakdown.sort((a, b) => b.totalCost - a.totalCost);

	// Determine time range
	const startTimes = calls.map(call => new Date(call.startTime).getTime());
	const endTimes = calls.map(call => new Date(call.endTime).getTime());
	
	const timeRange = {
		start: calls.length > 0 ? new Date(Math.min(...startTimes)).toISOString() : new Date().toISOString(),
		end: calls.length > 0 ? new Date(Math.max(...endTimes)).toISOString() : new Date().toISOString(),
	};

	return {
		calls,
		totalMinutes: Math.round(totalMinutes * 100) / 100,
		totalCost: Math.round(totalCost * 100) / 100,
		callCount,
		assistantBreakdown,
		timeRange,
	};
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

		// Allow unauthenticated requests for now (can be restricted later)
		if (!user) {
			console.log("[fetch-call-analytics] No user found, proceeding without authentication");
		}

		const requestData = await req.json();
		const { assistantId, startDate, endDate } = requestData;

		console.log("[fetch-call-analytics] Request:", { assistantId, startDate, endDate, user: user?.id });

		// Fetch calls from Vapi
		const calls = await fetchVapiCalls(assistantId, startDate, endDate);
		
		// Get assistant names
		const assistantNames = await getAssistantNames(calls);
		
		// Add assistant names to calls
		calls.forEach(call => {
			call.assistantName = assistantNames.get(call.assistantId) || `Assistant ${call.assistantId.slice(0, 8)}`;
		});

		// Calculate analytics
		const analytics = calculateAnalytics(calls, assistantNames);

		console.log("[fetch-call-analytics] Analytics calculated:", {
			callCount: analytics.callCount,
			totalMinutes: analytics.totalMinutes,
			totalCost: analytics.totalCost,
			assistantCount: analytics.assistantBreakdown.length,
		});

		return new Response(JSON.stringify(analytics), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	} catch (error: any) {
		console.error("[fetch-call-analytics] Error:", error);
		return new Response(JSON.stringify({ error: error.message || "Internal error" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
