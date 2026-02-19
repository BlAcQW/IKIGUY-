import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import "https://deno.land/x/xhr@0.1.0/mod.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

async function fetchSiteText(url?: string): Promise<string> {
	if (!url) return "";
	try {
		console.log("[create-assistant] Fetching site content from:", url);
		const res = await fetch(url, { headers: { "User-Agent": "AILabsAssistantBot/1.0" } });
		const html = await res.text();

		// Clean HTML and extract text
		const cleanText = html
			.replace(/<script[\s\S]*?<\/script>/gi, " ")
			.replace(/<style[\s\S]*?<\/style>/gi, " ")
			.replace(/<[^>]+>/g, " ")
			.replace(/\s+/g, " ")
			.trim();

		// Use Gemini 2.5 Pro to extract and summarize key information
		const geminiApiKey = Deno.env.get('GEMINI_API_KEY');
		if (!geminiApiKey) {
			console.warn("[create-assistant] No GEMINI_API_KEY found, using basic text extraction");
			return cleanText.slice(0, 5000);
		}

		try {
			console.log("[create-assistant] Using Gemini 2.5 Pro to extract site information");
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
				const extractedInfo = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text;
				if (extractedInfo) {
					console.log("[create-assistant] Gemini extraction successful, length:", extractedInfo.length);
					return extractedInfo;
				}
			} else {
				console.warn("[create-assistant] Gemini API failed:", geminiRes.status, await geminiRes.text());
			}
		} catch (geminiError) {
			console.error("[create-assistant] Gemini extraction error:", geminiError);
		}

		// Fallback to basic extraction
		console.log("[create-assistant] Using fallback text extraction");
		return cleanText.slice(0, 5000);
	} catch (error) {
		console.error("[create-assistant] Site fetch error:", error);
		return "";
	}
}

function buildPrompt(type: string, name: string, description: string, siteText: string, knowledgeBase?: string) {
	// Synthesize company information from website and knowledge base
	let companyContext = "";
	let serviceContext = "";
	let processContext = "";

	if (siteText || knowledgeBase) {
		const fullContext = `${siteText || ''}\n${knowledgeBase || ''}`.trim();

		// Extract company information
		const companyMatch = fullContext.match(/(?:company|business|organization)[\s:]+([\w\s&.,'-]+?)(?:\s+is|\s+offers|\s+provides|specializes|founded|established)/i);
		if (companyMatch) {
			companyContext = `You represent ${companyMatch[1].trim()}.`;
		}

		// Extract key services/products
		const serviceKeywords = fullContext.match(/(?:offers?|provides?|specializes?\s+in|services?\s+include|products?\s+include)[\s:]+([\w\s,.-]+?)(?:\.|$)/gi);
		if (serviceKeywords && serviceKeywords.length > 0) {
			const services = serviceKeywords.map(s => s.replace(/^(?:offers?|provides?|specializes?\s+in|services?\s+include|products?\s+include)[\s:]+/i, '').trim()).join(', ');
			serviceContext = `Key offerings include: ${services}.`;
		}

		// Extract process or contact information
		const contactMatch = fullContext.match(/(?:contact|call|email|phone)[\s:]+([+\d\s()-]+|[\w.-]+@[\w.-]+)/gi);
		const processMatch = fullContext.match(/(?:process|procedure|steps|how\s+to)[\s:]+([\w\s,.-]+?)(?:\.|$)/gi);

		if (contactMatch) {
			processContext += ` Contact information: ${contactMatch.join(', ')}.`;
		}
		if (processMatch) {
			processContext += ` Important processes: ${processMatch.map(p => p.replace(/^(?:process|procedure|steps|how\s+to)[\s:]+/i, '')).join('; ')}.`;
		}
	}

	// Build intelligent system prompt based on assistant type
	const typeMap = {
		sales_cold_call: 'sales cold call',
		help_desk: 'customer support',
		appointment_booking: 'appointment booking',
		lead_qualification: 'lead qualification',
		order_processing: 'order processing',
		general_inquiry: 'customer service'
	};

	const assistantRole = typeMap[type as keyof typeof typeMap] || 'customer service';

	// Combine description with extracted context intelligently
	const enhancedDescription = [
		description,
		companyContext,
		serviceContext,
		processContext
	].filter(Boolean).join(' ');

	const base = `You are a professional voice ${assistantRole} assistant named ${name}. ${enhancedDescription}
  
## Communication Guidelines:
- **Speak slowly** and clearly
- **Check in with the listener frequently** - ask questions like "Does that make sense?" or "Would you like me to explain more?"
- **Mention numbers naturally** (e.g., "four thousand" instead of "four zero zero zero")
- **Keep conversations engaging** rather than monologues - break information into digestible chunks
- Use warm, friendly, confident tone
- Listen carefully and respond contextually

## Conversation Style:
- Present information in small chunks and check interest after each point
- Always ask clarifying questions to better understand customer needs
- Be conversational, not scripted
- Show genuine interest in helping the customer`;

	// Define opening messages for different assistant types
	const openingMessages = {
		sales_cold_call: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how are you doing today?`,
		help_desk: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`,
		appointment_booking: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`,
		lead_qualification: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`,
		order_processing: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`,
		general_inquiry: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`,
		follow_up: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how are you doing today?`,
		survey: `Hello, this is ${name} from ${companyContext.replace('You represent ', '').replace('.', '') || 'our company'}, how may I help you today?`
	} as Record<string, string>;

	const goals = {
		sales_cold_call: "Introduce offering, qualify prospect, highlight benefits, and book a meeting or transfer to advisor.",
		help_desk: "Quickly understand issue, provide clear steps, and escalate when needed.",
		follow_up: "Gently follow up after prior interaction, confirm interest, and schedule next step.",
		survey: "Politely conduct a brief survey, collect answers accurately, and thank the user.",
		appointment_booking: "Help customers schedule appointments, confirm availability, and provide booking details.",
		lead_qualification: "Ask qualifying questions to understand needs, budget, and timeline before transferring to sales.",
		order_processing: "Assist with order placement, payment processing, and order tracking information.",
		general_inquiry: "Answer questions, provide information, and direct customers to appropriate resources."
	} as Record<string, string>;

	// Add specific context if there's additional valuable information
	let additionalContext = "";
	if (siteText || knowledgeBase) {
		const fullContext = `${siteText || ''}\n${knowledgeBase || ''}`.trim();
		// Only include raw context if it contains specific operational details not already extracted
		const hasSpecificDetails = fullContext.match(/(?:hours|location|pricing|policy|warranty|return|shipping|delivery)/i);
		if (hasSpecificDetails && fullContext.length < 1000) {
			additionalContext = `\n\n## Additional Context:\n${fullContext}`;
		}
	}

	const openingMessage = openingMessages[type] || openingMessages.general_inquiry;

	return `${base}

## Opening Message:
Always start conversations with: "${openingMessage}"

## Primary Goal:
${goals[type] || goals.general_inquiry}${additionalContext}`;
}

async function createVapiAssistant(name: string, systemPrompt: string, voiceId: string, useTemplate: boolean = false, knowledgeBaseFileIds: string[] = []) {
	const token = Deno.env.get("VAPI_PRIVATE_KEY");
	if (!token) throw new Error("Missing VAPI_PRIVATE_KEY");

	console.log("[create-assistant] Creating Vapi assistant", {
		name,
		voiceId,
		systemPromptLen: systemPrompt?.length || 0,
		useTemplate,
		tokenLength: token?.length || 0,
		tokenPrefix: token?.slice(0, 10) + "...",
	});

	const endpoint = "https://api.vapi.ai/assistant";

	let requestBody: any;

	if (useTemplate) {
		// Use the assistant template as base
		const templateId = "96037449-9dd1-49d9-a092-b8d088d2b5c9";

		console.log("[create-assistant] Fetching template:", templateId);

		// Fetch the template first
		const templateResponse = await fetch(`https://api.vapi.ai/assistant/${templateId}`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json',
			},
		});

		if (!templateResponse.ok) {
			const errorText = await templateResponse.text();
			console.error("[create-assistant] Template fetch failed:", templateResponse.status, errorText);
			throw new Error(`Failed to fetch template: ${templateResponse.status} - ${errorText}`);
		}

		const template = await templateResponse.json();
		console.log("[create-assistant] Template fetched:", {
			id: template.id,
			name: template.name,
			hasModel: !!template.model,
			hasVoice: !!template.voice
		});

		// Extract company name from the assistant name or use a default
		const companyName = name.includes(' ') ? name.split(' ').slice(1).join(' ') : name;

		// Create first message based on assistant type
		let firstMessage: string;
		if (name.toLowerCase().includes('help') || name.toLowerCase().includes('support')) {
			firstMessage = `Hello, I am ${name}. How may I help you today?`;
		} else {
			firstMessage = `Hello, I'm ${name}. How are you today?`;
		}

		// Get webhook URL from environment
		const webhookUrl = Deno.env.get("VAPI_WEBHOOK_URL") || "https://ljzbzjgvwzivpmlmuxhx.supabase.co/functions/v1/vapi-webhook";
		const webhookSecret = Deno.env.get("VAPI_WEBHOOK_SECRET") || "8b4e9d5f6a93c7e124ff28dbd4a1c672b8f930ca9a7e55e8d3b42f7c93a61fd2";

		// Create NEW assistant using template settings but with custom values
		// IMPORTANT: We're creating a NEW assistant, not modifying the template
		requestBody = {
			name, // New name
			firstMessage: firstMessage, // Custom first message
			model: {
				// Use template model settings but with our custom system prompt
				provider: template.model?.provider || "openai",
				model: template.model?.model || "gpt-4o-mini",
				messages: [{
					role: "system",
					content: systemPrompt // Our custom system prompt
				}]
			},
			voice: {
				// Use user's selected voice, not template voice
				provider: "vapi",
				voiceId: (voiceId || "paige").charAt(0).toUpperCase() + (voiceId || "paige").slice(1).toLowerCase()
			},
			// Use template settings for other configurations
			recordingEnabled: template.recordingEnabled !== undefined ? template.recordingEnabled : false,
			endCallPhrases: template.endCallPhrases || ["goodbye", "bye", "thank you"],
			// Configure webhook for real-time call events
			server: {
				url: webhookUrl,
				secret: webhookSecret
			},
			// Configure which server messages to receive
			serverMessages: [
				"conversation-update",
				"end-of-call-report",
				"function-call",
				"hang",
				"speech-update",
				"status-update",
				"transcript",
				"tool-calls",
				"transfer-destination-request",
				"handoff-destination-request",
				"user-interrupted"
			]
		};

		console.log("[create-assistant] Creating NEW assistant using template settings:", {
			name,
			firstMessage,
			systemPromptLength: systemPrompt.length,
			userVoiceId: voiceId,
			templateId: template.id,
			isNewAssistant: true
		});
	} else {
		// Original logic for non-template assistants
		const openingMessageMatch = systemPrompt.match(/Always start conversations with: "([^"]+)"/);
		const firstMessage = openingMessageMatch ? openingMessageMatch[1] : "Hello! How can I help you today?";

		// Get webhook URL from environment
		const webhookUrl = Deno.env.get("VAPI_WEBHOOK_URL") || "https://ljzbzjgvwzivpmlmuxhx.supabase.co/functions/v1/vapi-webhook";
		const webhookSecret = Deno.env.get("VAPI_WEBHOOK_SECRET") || "8b4e9d5f6a93c7e124ff28dbd4a1c672b8f930ca9a7e55e8d3b42f7c93a61fd2";

		requestBody = {
			name,
			firstMessage: firstMessage,
			model: {
				provider: "openai",
				model: "gpt-4o-mini",
				messages: [{
					role: "system",
					content: systemPrompt
				}]
			},
			voice: {
				provider: "vapi",
				voiceId: (voiceId || "paige").charAt(0).toUpperCase() + (voiceId || "paige").slice(1).toLowerCase()
			},
			recordingEnabled: false,
			endCallPhrases: ["goodbye", "bye", "thank you"],
			// Configure webhook for real-time call events
			server: {
				url: webhookUrl,
				secret: webhookSecret
			},
			// Configure which server messages to receive
			serverMessages: [
				"conversation-update",
				"end-of-call-report",
				"function-call",
				"hang",
				"speech-update",
				"status-update",
				"transcript",
				"tool-calls",
				"transfer-destination-request",
				"handoff-destination-request",
				"user-interrupted"
			]
		};
	}

	console.log("[create-assistant] Request details:", {
		endpoint,
		method: "POST",
		bodyKeys: Object.keys(requestBody),
		hasAuth: !!token
	});

	// IMPORTANT: We're making a POST request to create a NEW assistant
	// This will generate a completely new assistant ID, not modify the template
	let res: Response;
	try {
		res = await fetch(endpoint, {
			method: "POST", // Creates new assistant with new ID
			headers: {
				"Authorization": `Bearer ${token}`,
				"Content-Type": "application/json",
			},
			body: JSON.stringify(requestBody),
		});
	} catch (err) {
		console.error("[create-assistant] Vapi fetch error", err);
		throw err;
	}

	console.log("[create-assistant] Vapi response", {
		status: res.status,
		statusText: res.statusText,
		headers: Object.fromEntries(res.headers.entries())
	});

	if (!res.ok) {
		const t = await res.text();
		console.error("[create-assistant] Vapi error body:", t);
		console.error("[create-assistant] Request body was:", JSON.stringify(requestBody, null, 2));
		throw new Error(`Vapi create assistant failed: ${t}`);
	}

	const data = await res.json();
	console.log("[create-assistant] Vapi response data:", JSON.stringify(data, null, 2));

	const createdId = data?.id || data?.assistant?.id || data?.data?.id;
	console.log("[create-assistant] Vapi assistant created", { id: createdId });

	// Create query tool for knowledge base if files are provided
	if (knowledgeBaseFileIds.length > 0) {
		try {
			console.log("[create-assistant] Creating query tool for knowledge base files:", knowledgeBaseFileIds);

			const queryToolBody = {
				type: "query",
				assistantId: createdId,
				query: {
					provider: "google",
					model: "gemini-2.5-pro",
					fileIds: knowledgeBaseFileIds
				}
			};

			const toolResponse = await fetch("https://api.vapi.ai/tool", {
				method: "POST",
				headers: {
					"Authorization": `Bearer ${token}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify(queryToolBody),
			});

			if (!toolResponse.ok) {
				const errorText = await toolResponse.text();
				console.warn("[create-assistant] Query tool creation failed:", toolResponse.status, errorText);
			} else {
				const toolData = await toolResponse.json();
				console.log("[create-assistant] Query tool created successfully:", toolData.id);
			}
		} catch (toolError) {
			console.warn("[create-assistant] Failed to create query tool:", toolError);
		}
	}

	return { id: createdId };
}

function slugify(input: string) {
	return input.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)+/g, "");
}

function generateFallbackHtml(assistantName: string, assistantId: string, description: string, websiteUrl: string) {
	const slug = assistantName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
	
	return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${assistantName} - AI Voice Assistant Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 10px; }
        .description { text-align: center; color: #666; margin-bottom: 40px; font-size: 18px; }
        .demo-section { text-align: center; padding: 40px 0; }
        .call-button { background: #4F46E5; color: white; border: none; padding: 15px 30px; border-radius: 25px; font-size: 18px; cursor: pointer; transition: background 0.3s; }
        .call-button:hover { background: #3730A3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>${assistantName}</h1>
        <p class="description">${description}</p>
        
        <div class="demo-section">
            <p>Click the button below to start a voice conversation with ${assistantName}</p>
            <button class="call-button" onclick="startCall()">🎤 Talk to ${assistantName}</button>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/index.js"></script>
    <script>
        const assistantId = '${assistantId}';
        
        async function startCall() {
            try {
                const call = await VapiWeb.start({
                    assistantId: assistantId,
                    config: {
                        inputAudioTranscription: {
                            model: 'nova-2',
                            language: 'en-US'
                        },
                        outputAudioSynthesis: {
                            model: 'nova-2',
                            voiceId: 'paige'
                        }
                    }
                });
                
                console.log('Call started:', call);
            } catch (error) {
                console.error('Error starting call:', error);
                alert('Error starting call. Please try again.');
            }
        }
    </script>
</body>
</html>`;
}


serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response(null, { headers: corsHeaders });
	}

	try {
		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
		const supabaseServiceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

		const supabaseAuth = createClient(supabaseUrl, supabaseAnonKey, {
			global: { headers: { Authorization: req.headers.get("Authorization") || "" } },
		});

		const {
			data: { user },
		} = await supabaseAuth.auth.getUser();

		// Check for guest mode credentials
		const requestData = await req.json();
		const { guestEmail, guestPassword, systemPromptOverride, useTemplate = false } = requestData;

		// Allow unauthenticated requests if guest credentials are provided
		if (!user && (!guestEmail || !guestPassword)) {
			return new Response(JSON.stringify({ error: "Unauthorized - Please provide guest credentials or authenticate" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		const { assistantName, description, websiteUrl, assistantType, voiceId, knowledgeBaseFileIds = [] } = requestData;

		console.log("[create-assistant] Request body", {
			assistantName,
			assistantType,
			voiceId,
			websiteUrl,
			knowledgeBaseCount: knowledgeBaseFileIds.length,
			useTemplate
		});

		const siteText = await fetchSiteText(websiteUrl);

		// Process knowledge base files
		let knowledgeBase = "";
		if (knowledgeBaseFileIds.length > 0) {
			try {
				console.log("[create-assistant] Processing knowledge base files:", knowledgeBaseFileIds);

				// For now, we'll create a query tool with the file IDs
				// The actual file content will be accessed by the assistant through the query tool
				knowledgeBase = `Knowledge base files have been uploaded and are available for reference. File IDs: ${knowledgeBaseFileIds.join(', ')}`;

				console.log("[create-assistant] Knowledge base processed, length:", knowledgeBase.length);
			} catch (e) {
				console.warn("[create-assistant] Failed to process knowledge base:", e);
			}
		}

		// Use system prompt override if provided, otherwise build from components
		const systemPrompt = systemPromptOverride || buildPrompt(assistantType, assistantName, description, siteText, knowledgeBase);
		console.log("[create-assistant] System prompt length", systemPrompt.length, "using override:", !!systemPromptOverride);

		const { id: assistantId } = await createVapiAssistant(assistantName, systemPrompt, voiceId || "paige", useTemplate, knowledgeBaseFileIds);
		console.log("[create-assistant] Assistant ID", assistantId);

		// Generate HTML demo via the new edge function
		console.log("[create-assistant] Calling generate-demo-html function");
		console.log("[create-assistant] Supabase URL:", supabaseUrl);
		console.log("[create-assistant] Assistant data for HTML generation:", {
			assistantName,
			assistantId,
			assistantType,
			siteContentLength: siteText?.length || 0,
			websiteUrl
		});

		// Call generate-demo-html directly using fetch (no auth required)
		const generateHtmlUrl = `${supabaseUrl}/functions/v1/generate-demo-html`;
		console.log("[create-assistant] Calling URL:", generateHtmlUrl);

		const htmlRequestData = {
			assistantName,
			assistantId,
			assistantType,
			siteContent: siteText,
			websiteUrl
		};
		console.log("[create-assistant] Request body for HTML generation:", htmlRequestData);

		try {
			const generateHtmlRes = await fetch(generateHtmlUrl, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${supabaseAnonKey}`,
				},
				body: JSON.stringify(htmlRequestData)
			});

			console.log("[create-assistant] HTML generation response status:", generateHtmlRes.status);
			console.log("[create-assistant] HTML generation response headers:", Object.fromEntries(generateHtmlRes.headers.entries()));

			if (!generateHtmlRes.ok) {
				const errorText = await generateHtmlRes.text();
				console.error("[create-assistant] HTML generation failed:", generateHtmlRes.status, errorText);
				// Don't throw error, just log it and continue with fallback HTML
				console.log("[create-assistant] Using fallback HTML generation");
			} else {
				const htmlGenRes = await generateHtmlRes.json();
				console.log("[create-assistant] HTML generation response data:", {
					hasHtml: !!htmlGenRes.html,
					htmlLength: htmlGenRes.html?.length || 0,
					responseKeys: Object.keys(htmlGenRes)
				});

				if (htmlGenRes.html) {
					console.log("[create-assistant] HTML generated successfully, length:", htmlGenRes.html.length);
					// Return the HTML and assistant data for frontend to handle deployment
					console.log("[create-assistant] Returning HTML for frontend deployment");

					return new Response(JSON.stringify({
						assistant_id: assistantId,
						html: htmlGenRes.html,
						status: "created"
					}), {
						headers: { ...corsHeaders, "Content-Type": "application/json" },
					});
				}
			}
		} catch (htmlError) {
			console.error("[create-assistant] HTML generation error:", htmlError);
			console.log("[create-assistant] Using fallback HTML generation");
		}

		// Fallback HTML generation
		console.log("[create-assistant] Generating fallback HTML");
		const fallbackHtml = generateFallbackHtml(assistantName, assistantId, description, websiteUrl);
		console.log("[create-assistant] Fallback HTML generated, length:", fallbackHtml.length);

		// Return the HTML and assistant data for frontend to handle deployment
		console.log("[create-assistant] Returning fallback HTML for frontend deployment");

		return new Response(JSON.stringify({
			assistant_id: assistantId,
			html: fallbackHtml,
			status: "created"
		}), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	} catch (error: any) {
		console.error("create-assistant error:", { message: error?.message, stack: error?.stack });
		return new Response(JSON.stringify({ error: error?.message || "Internal error" }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
