import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import "https://deno.land/x/xhr@0.1.0/mod.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

async function extractSiteContent(url: string): Promise<{ title: string; description: string; content: string }> {
	try {
		console.log("[extract-site-info] Fetching site content from:", url);

		// Add timeout and better error handling
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

		const res = await fetch(url, {
			headers: {
				"User-Agent": "Mozilla/5.0 (compatible; AILabsAssistantBot/1.0; +https://ailabs.africa)",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
				"Accept-Language": "en-US,en;q=0.5",
				"Accept-Encoding": "gzip, deflate",
				"Connection": "keep-alive",
				"Upgrade-Insecure-Requests": "1"
			},
			signal: controller.signal,
			redirect: "follow"
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		const html = await res.text();
		console.log("[extract-site-info] Successfully fetched HTML, length:", html.length);

		// Extract title
		const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
		const title = titleMatch ? titleMatch[1].trim() : "Website";

		// Extract meta description
		const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i);
		const description = descMatch ? descMatch[1].trim() : "";

		// Clean HTML and extract text
		const cleanText = html
			.replace(/<script[\s\S]*?<\/script>/gi, " ")
			.replace(/<style[\s\S]*?<\/style>/gi, " ")
			.replace(/<[^>]+>/g, " ")
			.replace(/\s+/g, " ")
			.trim();

		console.log("[extract-site-info] Cleaned text length:", cleanText.length);

		// Use Gemini 2.5 Pro for intelligent content extraction
		const geminiApiKey = Deno.env.get('GEMINI_API_KEY');
		if (!geminiApiKey) {
			console.warn("[extract-site-info] No GEMINI_API_KEY found, using basic text extraction");
			return {
				title,
				description: description || "Website content",
				content: cleanText.slice(0, 5000)
			};
		}

		try {
			console.log("[extract-site-info] Using Gemini 2.5 Pro to extract site information");
			const geminiRes = await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"x-goog-api-key": geminiApiKey,
				},
				body: JSON.stringify({
					contents: [{
						parts: [{
							text: `Extract and summarize the key information from this website content for an AI voice assistant. Focus on: company/business description, services/products offered, contact information, key features, pricing if mentioned, and any important details a customer service AI should know. Keep it concise but comprehensive (max 2000 words):\n\n${cleanText.slice(0, 20000)}`
						}]
					}],
					generationConfig: {
						temperature: 0.1,
						maxOutputTokens: 2048,
					}
				}),
			});

			if (geminiRes.ok) {
				const geminiData = await geminiRes.json();
				console.log("[extract-site-info] Gemini response:", JSON.stringify(geminiData, null, 2));

				const extractedInfo = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text;
				if (extractedInfo) {
					console.log("[extract-site-info] Gemini extraction successful, length:", extractedInfo.length);
					return {
						title,
						description: description || "AI-extracted website information",
						content: extractedInfo
					};
				} else {
					console.warn("[extract-site-info] No text found in Gemini response");
				}
			} else {
				const errorText = await geminiRes.text();
				console.warn("[extract-site-info] Gemini API failed:", geminiRes.status, errorText);

				// Check for specific Gemini API errors
				if (geminiRes.status === 400) {
					console.error("[extract-site-info] Bad request - check API key and request format");
				} else if (geminiRes.status === 403) {
					console.error("[extract-site-info] Forbidden - API key may be invalid or quota exceeded");
				} else if (geminiRes.status === 429) {
					console.error("[extract-site-info] Rate limited - too many requests");
				}
			}
		} catch (geminiError) {
			console.error("[extract-site-info] Gemini extraction error:", geminiError);
		}

		// Fallback to basic extraction
		console.log("[extract-site-info] Using fallback text extraction");
		return {
			title,
			description: description || "Website content",
			content: cleanText.slice(0, 5000)
		};

	} catch (error) {
		console.error("[extract-site-info] Site fetch error:", error);

		// Provide more specific error messages
		if (error.name === 'AbortError') {
			throw new Error('Request timeout: Website took too long to respond');
		} else if (error.message?.includes('Failed to fetch')) {
			throw new Error('Network error: Unable to connect to the website');
		} else if (error.message?.includes('HTTP 403')) {
			throw new Error('Access denied: Website blocked our request');
		} else if (error.message?.includes('HTTP 404')) {
			throw new Error('Page not found: The website URL appears to be invalid');
		} else if (error.message?.includes('HTTP 5')) {
			throw new Error('Server error: The website is experiencing technical difficulties');
		}

		throw new Error(`Failed to extract site information: ${error.message}`);
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

		// Try to get user, but don't fail if no auth header (for testing)
		let user = null;
		try {
			const { data: { user: authUser } } = await supabaseAuth.auth.getUser();
			user = authUser;
		} catch (authError) {
			console.log("[extract-site-info] No valid auth token, proceeding without authentication");
		}

		// For now, allow unauthenticated requests (for testing)
		// if (!user) {
		// 	return new Response(JSON.stringify({ error: "Unauthorized" }), {
		// 		status: 401,
		// 		headers: { ...corsHeaders, "Content-Type": "application/json" },
		// 	});
		// }

		const { url } = await req.json();

		if (!url) {
			return new Response(JSON.stringify({ error: "URL is required" }), {
				status: 400,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		console.log("[extract-site-info] Request to extract from:", url);

		const siteInfo = await extractSiteContent(url);

		return new Response(JSON.stringify(siteInfo), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});

	} catch (error: any) {
		console.error("extract-site-info error:", { message: error?.message, stack: error?.stack });
		return new Response(JSON.stringify({ error: error?.message || "Internal error" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});