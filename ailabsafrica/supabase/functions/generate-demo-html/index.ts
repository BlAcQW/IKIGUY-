import { serve } from "https://deno.land/std@0.190.0/http/server.ts";

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface GenerateHtmlRequest {
	assistantName: string;
	assistantId: string;
	assistantType: string;
	siteContent: string;
	websiteUrl?: string;
}

async function generateDemoHtmlWithGemini(assistantName: string, assistantId: string, assistantType: string, siteContent: string, websiteUrl?: string): Promise<string> {
	console.log("[generate-demo-html] Starting HTML generation with params:", {
		assistantName,
		assistantId,
		assistantType,
		siteContentLength: siteContent?.length || 0,
		websiteUrl
	});

	const geminiApiKey = Deno.env.get('GEMINI_API_KEY');
	const pubKey = Deno.env.get("VAPI_PUBLIC_API_KEY") || "0c22dcea-0d6c-4fc0-8fb2-93292d8575e8";

	console.log("[generate-demo-html] Checking Gemini API key availability:", {
		hasGeminiKey: !!geminiApiKey,
		keyLength: geminiApiKey?.length || 0,
		assistantName,
		assistantId,
		pubKey: pubKey.substring(0, 10) + "..."
	});

	if (!geminiApiKey) {
		console.warn("[generate-demo-html] No GEMINI_API_KEY found, using fallback HTML");
		const fallbackHtml = buildFallbackHtml(assistantName, assistantId, siteContent);
		console.log("[generate-demo-html] Fallback HTML generated, length:", fallbackHtml.length);
		return fallbackHtml;
	}

	// Extract company name from website URL or site content
	let companyName = "Company";
	if (websiteUrl) {
		const urlMatch = websiteUrl.match(/(?:https?:\/\/)?(?:www\.)?([^\/]+)/);
		if (urlMatch) {
			companyName = urlMatch[1].split('.')[0];
		}
	}

	// If we have site content, try to extract company name from it
	if (siteContent) {
		const nameMatch = siteContent.match(/(?:company|business|organization)[\s:]+([\w\s&]+?)(?:\s+is|\s+offers|\s+provides|\.)/i);
		if (nameMatch) {
			companyName = nameMatch[1].trim();
		}
	}

	// Map assistant type to user-friendly description
	const assistantTypeMap = {
		'sales': 'sales assistant',
		'help_desk': 'customer support assistant',
		'appointment_booking': 'appointment booking assistant',
		'lead_qualification': 'lead qualification assistant',
		'order_processing': 'ordering assistant',
		'general_inquiry': 'assistant'
	};

	const assistantDescription = assistantTypeMap[assistantType as keyof typeof assistantTypeMap] || 'assistant';

	const prompt = `You are generating a professional landing page for ${companyName}, featuring their AI ${assistantDescription} named "${assistantName}".

COMPANY INFORMATION:
${siteContent || 'No specific website information available'}

CRITICAL WIDGET REQUIREMENT - THIS IS MANDATORY:
You MUST include the EXACT Vapi widget code provided below. DO NOT create any custom JavaScript. DO NOT use window.Vapi, vapi.start(), or any other implementation. The widget code below is REQUIRED and CANNOT be modified in any way.

EXACT WIDGET CODE TO COPY (DO NOT CHANGE ANYTHING):
<vapi-widget
  public-key="${pubKey}"
  assistant-id="${assistantId}"
  mode="voice"
  theme="dark"
  base-bg-color="#000000"
  accent-color="#14B8A6"
  cta-button-color="#000000"
  cta-button-text-color="#ffffff"
  border-radius="large"
  size="full"
  position="bottom-right"
  title="Talk to ${assistantName}"
  start-button-text="Start Call"
  end-button-text="End Call"
  chat-first-message="Hello! How can I help you today?"
  chat-placeholder="Type your message..."
  voice-show-transcript="true"
  consent-required="true"
  consent-title="Terms and conditions"
  consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
  consent-storage-key="vapi_widget_consent"
></vapi-widget>

<script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>

FORBIDDEN - DO NOT USE:
- new window.Vapi()
- vapi.start()
- cdn.jsdelivr.net
- onclick handlers for calls
- placeholder API keys
- any custom JavaScript for Vapi

DESIGN REQUIREMENTS:
1. Create a modern, professional landing page
2. Use Tailwind CSS via CDN
3. Include compelling copy based on company information
4. Add 4 relevant service cards for their business
5. Use appropriate industry colors
6. Place the EXACT widget code at the end of body tag
7. Make it conversion-focused and visually appealing

WEBSITE URL: ${websiteUrl || 'Not provided'}

Generate ONLY the complete HTML page with the exact widget code included. Do not add explanations.`;

	try {
		console.log("[generate-demo-html] Using Gemini 2.5 Pro to generate HTML demo");
		console.log("[generate-demo-html] Prompt length:", prompt.length);
		console.log("[generate-demo-html] Prompt preview (first 500 chars):", prompt.substring(0, 500));

		const geminiRes = await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"x-goog-api-key": geminiApiKey,
			},
			body: JSON.stringify({
				contents: [{
					parts: [{
						text: prompt
					}]
				}],
				generationConfig: {
					temperature: 0.3,
					maxOutputTokens: 8192,
				}
			}),
		});

		console.log("[generate-demo-html] Gemini API response status:", geminiRes.status);
		console.log("[generate-demo-html] Gemini API response headers:", Object.fromEntries(geminiRes.headers.entries()));

		if (geminiRes.ok) {
			const geminiData = await geminiRes.json();
			console.log("[generate-demo-html] Gemini API response data keys:", Object.keys(geminiData));
			console.log("[generate-demo-html] Gemini API candidates:", geminiData?.candidates?.length || 0);

			const generatedHtml = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text;
			if (generatedHtml) {
				console.log("[generate-demo-html] Gemini HTML generation successful, length:", generatedHtml.length);
				console.log("[generate-demo-html] Generated HTML preview (first 200 chars):", generatedHtml.substring(0, 200));
				// Clean up any markdown formatting that might have been added
				const cleanHtml = generatedHtml
					.replace(/^html\n/g, '')  // Remove 'html\n' prefix
					.replace(/```html\n?/g, '')
					.replace(/```\n?$/g, '')
					.trim();
				console.log("[generate-demo-html] Cleaned HTML length:", cleanHtml.length);
				return cleanHtml;
			} else {
				console.error("[generate-demo-html] No HTML content in Gemini response:", geminiData);
			}
		} else {
			const errorText = await geminiRes.text();
			console.warn("[generate-demo-html] Gemini HTML generation failed:", geminiRes.status, errorText);
		}
	} catch (geminiError) {
		console.error("[generate-demo-html] Gemini HTML generation error:", geminiError);
		console.error("[generate-demo-html] Gemini error stack:", geminiError.stack);
	}

	// Fallback to basic HTML generation
	console.log("[generate-demo-html] Using fallback HTML generation");
	const fallbackHtml = buildFallbackHtml(assistantName, assistantId, siteContent);
	console.log("[generate-demo-html] Fallback HTML generated, length:", fallbackHtml.length);
	return fallbackHtml;
}

function buildFallbackHtml(title: string, assistantId: string, siteContent: string): string {
	console.log("[generate-demo-html] Building fallback HTML with params:", { title, assistantId, siteContentLength: siteContent?.length || 0 });

	const pubKey = Deno.env.get("VAPI_PUBLIC_API_KEY") || "0c22dcea-0d6c-4fc0-8fb2-93292d8575e8";
	console.log("[generate-demo-html] Using pubKey:", pubKey.substring(0, 10) + "...");

	// Extract company name from title or site content
	let companyName = "Company";
	const titleParts = title.split(" from ");
	if (titleParts.length > 1) {
		companyName = titleParts[1];
	}
	console.log("[generate-demo-html] Extracted company name:", companyName);

	// Extract key services/features from site content
	const features = [];
	if (siteContent) {
		// Common service patterns
		if (siteContent.match(/(?:pizza|food|restaurant|delivery|order)/i)) {
			features.push(
				{ icon: "fas fa-pizza-slice", title: "Delicious Pizza", desc: "Enjoy a wide variety of pizza toppings, from classic Pepperoni to Swiss Mushroom and more!" },
				{ icon: "fas fa-truck", title: "Fast Delivery", desc: "Get your favorite pizza delivered right to your doorstep. Order online and track your order in real-time." },
				{ icon: "fas fa-store", title: "Easy Pickup", desc: "Order online and pick up your pizza at your nearest location. Convenient and quick!" },
				{ icon: "fas fa-laptop", title: "Online Ordering", desc: "Order your favorite pizza online through our website. It's easy, fast, and secure!" }
			);
		} else if (siteContent.match(/(?:bank|finance|loan|account|investment)/i)) {
			features.push(
				{ icon: "fas fa-university", title: "Bank Accounts", desc: "Comprehensive banking solutions for your financial needs." },
				{ icon: "fas fa-coins", title: "Loans & Credit", desc: "Flexible financing options to help achieve your goals." },
				{ icon: "fas fa-chart-line", title: "Investments", desc: "Grow your wealth with expert-managed investment products." },
				{ icon: "fas fa-shield-alt", title: "Security", desc: "Advanced security measures to protect your finances." }
			);
		} else if (siteContent.match(/(?:insurance|coverage|policy|claim)/i)) {
			features.push(
				{ icon: "fas fa-shield-alt", title: "Insurance Coverage", desc: "Comprehensive protection for you and your family." },
				{ icon: "fas fa-clipboard-check", title: "Easy Claims", desc: "Simple and fast claims processing when you need it most." },
				{ icon: "fas fa-headset", title: "Expert Support", desc: "Dedicated support team to guide you through your options." },
				{ icon: "fas fa-phone", title: "24/7 Service", desc: "Round-the-clock assistance for all your insurance needs." }
			);
		} else {
			// Generic business features
			features.push(
				{ icon: "fas fa-bullseye", title: "Expert Service", desc: "Professional assistance tailored to your specific needs." },
				{ icon: "fas fa-bolt", title: "Quick Response", desc: "Fast and efficient service to resolve your inquiries." },
				{ icon: "fas fa-comments", title: "Personal Support", desc: "Dedicated support team available to help you succeed." },
				{ icon: "fas fa-handshake", title: "Trusted Partner", desc: "Reliable service you can count on for all your needs." }
			);
		}
	} else {
		// Default features
		features.push(
			{ icon: "fas fa-bullseye", title: "Expert Service", desc: "Professional assistance tailored to your specific needs." },
			{ icon: "fas fa-bolt", title: "Quick Response", desc: "Fast and efficient service to resolve your inquiries." },
			{ icon: "fas fa-comments", title: "Personal Support", desc: "Dedicated support team available to help you succeed." },
			{ icon: "fas fa-handshake", title: "Trusted Partner", desc: "Reliable service you can count on for all your needs." }
		);
	}

	// Extract contact information
	const phoneMatch = siteContent?.match(/\+?[\d\s()-]{10,}/);
	const websiteMatch = siteContent?.match(/https?:\/\/[^\s]+/);

	return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${companyName} - AI Voice Assistant Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style>
        body {
            font-family: sans-serif;
        }
        .hero {
            background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2126&q=80');
            background-size: cover;
            background-position: center;
            color: white;
        }
    </style>
</head>
<body class="bg-gray-100">

    <!-- Hero Section -->
    <header class="hero py-20 text-center">
        <div class="container mx-auto">
            <h1 class="text-5xl font-bold mb-4">Talk to ${title}</h1>
            <p class="text-xl mb-8">Experience intelligent conversation with our AI assistant. Get expert help and support through voice interaction.</p>
            <a href="#contact" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-full">Get Started</a>
        </div>
    </header>

    <!-- Services Section -->
    <section class="py-12">
        <div class="container mx-auto">
            <h2 class="text-3xl font-bold text-center mb-8 text-gray-800">Our Services</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                ${features.map(feature => `
                <!-- Service Card -->
                <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
                    <i class="${feature.icon} text-3xl text-blue-600 mb-4"></i>
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">${feature.title}</h3>
                    <p class="text-gray-600">${feature.desc}</p>
                </div>
                `).join('')}

            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="bg-gray-200 py-12">
        <div class="container mx-auto text-center">
            <h2 class="text-3xl font-bold text-gray-800 mb-6">Contact Us</h2>
            <p class="text-gray-700 mb-4">Ready to experience AI assistance? Start a conversation with ${title}.</p>
            ${phoneMatch ? `<p class="text-gray-700 mb-2">Phone: ${phoneMatch[0]}</p>` : ''}
            ${websiteMatch ? `<a href="${websiteMatch[0]}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-full">Visit Our Website</a>` : ''}
        </div>
    </section>

    <!-- Footer Section -->
    <footer class="bg-gray-800 text-white py-4 text-center">
        <p>&copy; 2025 ${companyName}. All rights reserved.</p>
    </footer>

<vapi-widget
  public-key="${pubKey}"
  assistant-id="${assistantId}"
  mode="voice"
  theme="dark"
  base-bg-color="#000000"
  accent-color="#14B8A6"
  cta-button-color="#000000"
  cta-button-text-color="#ffffff"
  border-radius="large"
  size="full"
  position="bottom-right"
  title="Talk to ${title}"
  start-button-text="Start Call"
  end-button-text="End Call"
  chat-first-message="Hello! How can I help you today?"
  chat-placeholder="Type your message..."
  voice-show-transcript="true"
  consent-required="true"
  consent-title="Terms and conditions"
  consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
  consent-storage-key="vapi_widget_consent"
></vapi-widget>

<script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js" async type="text/javascript"></script>
</body>
</html>`;

	console.log("[generate-demo-html] Fallback HTML built successfully, length:", html.length);
	return html;
}

// Helper function to generate brand colors based on company name
function getBrandColor(companyName: string): { primary: string; secondary: string; light: string } {
	const colors = [
		{ primary: '#003366', secondary: '#004080', light: 'rgba(0, 51, 102, 0.08)' }, // Blue
		{ primary: '#8B5CF6', secondary: '#A78BFA', light: 'rgba(139, 92, 246, 0.08)' }, // Purple
		{ primary: '#059669', secondary: '#10B981', light: 'rgba(5, 150, 105, 0.08)' }, // Green
		{ primary: '#DC2626', secondary: '#EF4444', light: 'rgba(220, 38, 38, 0.08)' }, // Red
		{ primary: '#D97706', secondary: '#F59E0B', light: 'rgba(217, 119, 6, 0.08)' }, // Orange
		{ primary: '#7C3AED', secondary: '#8B5CF6', light: 'rgba(124, 58, 237, 0.08)' }, // Indigo
	];

	// Simple hash function to pick consistent colors based on company name
	let hash = 0;
	for (let i = 0; i < companyName.length; i++) {
		hash = companyName.charCodeAt(i) + ((hash << 5) - hash);
	}
	return colors[Math.abs(hash) % colors.length];
}

serve(async (req) => {
	console.log("[generate-demo-html] Function called with method:", req.method);
	console.log("[generate-demo-html] Request headers:", Object.fromEntries(req.headers.entries()));

	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		console.log("[generate-demo-html] Handling CORS preflight request");
		return new Response(null, { headers: corsHeaders });
	}

	try {
		console.log("[generate-demo-html] Parsing request body...");
		const { assistantName, assistantId, assistantType, siteContent, websiteUrl }: GenerateHtmlRequest = await req.json();

		console.log("[generate-demo-html] Request received:", {
			assistantName,
			assistantId,
			assistantType,
			siteContentLength: siteContent?.length || 0,
			websiteUrl,
			hasAssistantName: !!assistantName,
			hasAssistantId: !!assistantId,
			hasAssistantType: !!assistantType
		});

		// Validate required fields
		if (!assistantName || !assistantId || !assistantType) {
			console.error("[generate-demo-html] Missing required fields:", { assistantName, assistantId, assistantType });
			return new Response(JSON.stringify({ error: "Missing required fields: assistantName, assistantId, assistantType" }), {
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' },
			});
		}

		console.log("[generate-demo-html] Starting HTML generation...");
		// Generate HTML using Gemini or fallback
		const html = await generateDemoHtmlWithGemini(assistantName, assistantId, assistantType, siteContent, websiteUrl);

		console.log("[generate-demo-html] HTML generation completed, length:", html.length);
		console.log("[generate-demo-html] HTML preview (first 200 chars):", html.substring(0, 200));

		const response = { html };
		console.log("[generate-demo-html] Sending response with html length:", response.html.length);

		return new Response(JSON.stringify(response), {
			headers: { ...corsHeaders, 'Content-Type': 'application/json' },
		});
	} catch (error) {
		console.error('[generate-demo-html] Error:', error);
		console.error('[generate-demo-html] Error stack:', error.stack);
		return new Response(JSON.stringify({ error: error.message }), {
			status: 500,
			headers: { ...corsHeaders, 'Content-Type': 'application/json' },
		});
	}
});