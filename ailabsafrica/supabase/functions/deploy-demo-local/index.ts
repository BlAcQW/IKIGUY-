import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface DeployDemoRequest {
	assistantName: string;
	assistantId: string;
	assistantType: string;
	html: string;
	userEmail?: string;
	guestEmail?: string;
}

serve(async (req) => {
	console.log("[deploy-demo-local] Function called with method:", req.method);
	console.log("[deploy-demo-local] Request headers:", Object.fromEntries(req.headers.entries()));

	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		console.log("[deploy-demo-local] Handling CORS preflight request");
		return new Response(null, { headers: corsHeaders });
	}

	try {
		console.log("[deploy-demo-local] Parsing request body...");
		const { assistantName, assistantId, assistantType, html, userEmail, guestEmail }: DeployDemoRequest = await req.json();

		console.log("[deploy-demo-local] Request received:", {
			assistantName,
			assistantId,
			assistantType,
			htmlLength: html?.length || 0,
			userEmail,
			guestEmail
		});

		// Validate required fields
		if (!assistantName || !assistantId || !assistantType || !html) {
			console.error("[deploy-demo-local] Missing required fields:", { assistantName, assistantId, assistantType, hasHtml: !!html });
			return new Response(JSON.stringify({ error: "Missing required fields: assistantName, assistantId, assistantType, html" }), {
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' },
			});
		}

		// Generate a unique ID for the demo file
		const demoId = `${assistantId}-${Date.now()}`;
		const fileName = `${demoId}.html`;
		const localPath = `/var/www/ailabsafrica/demos/${fileName}`;
		const demoUrl = `https://ailabsafrica.com/demos/${fileName}`;

		console.log("[deploy-demo-local] Creating local file:", {
			fileName,
			localPath,
			demoUrl,
			htmlLength: html.length
		});

		// Check if we have a writable demos directory
		const demosDir = "/var/www/ailabsafrica/demos";
		const fallbackDemosDir = "/tmp/demos";
		let actualDemosDir = demosDir;
		let actualDemoUrl = demoUrl;

		// Try to create demos directory if it doesn't exist
		try {
			// This is a fallback approach - we'll use a different strategy
			console.log("[deploy-demo-local] Using API deployment approach");
		} catch (dirError) {
			console.warn("[deploy-demo-local] Could not access demos directory, using fallback:", dirError);
			actualDemosDir = fallbackDemosDir;
			actualDemoUrl = `https://ailabsafrica.com/demo-preview?id=${demoId}`;
		}

		// Try to deploy via API endpoint first, fallback to database storage
		let deployed = false;
		let finalDemoUrl = actualDemoUrl;

		try {
			const configuredBase = (Deno.env.get("DEPLOY_API_BASE") || "").replace(/\/$/, "");
			const candidateEndpoints = [
				configuredBase ? `${configuredBase}/deploy-demo` : undefined,
				"https://api.ailabsafrica.com/deploy-demo",
				"https://ailabsafrica.com/deploy-demo",
			].filter(Boolean) as string[];

			console.log("[deploy-demo-local] Trying API deployment endpoints:", candidateEndpoints);

			for (const endpoint of candidateEndpoints) {
				try {
					console.log("[deploy-demo-local] Trying endpoint:", endpoint);
					const apiResponse = await fetch(endpoint, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
							'Authorization': `Bearer ${Deno.env.get("API_DEPLOY_KEY") || ""}`,
						},
						body: JSON.stringify({
							fileName,
							html,
							demoId,
							assistantName,
							assistantType
						})
					});

					if (apiResponse.ok) {
						const apiResult = await apiResponse.json();
						console.log("[deploy-demo-local] API deployment successful:", apiResult);
						if (apiResult?.success) {
							deployed = true;
							break;
						}
					} else {
						const errorText = await apiResponse.text();
						console.warn("[deploy-demo-local] API deployment failed:", apiResponse.status, errorText);
					}
				} catch (attemptError) {
					console.warn("[deploy-demo-local] Deploy attempt failed:", (attemptError as Error)?.message || attemptError);
				}
			}
		} catch (apiError) {
			console.warn("[deploy-demo-local] API deployment failed, will use database fallback:", apiError);
		}

		// If API deployment failed, store in database as fallback
		if (!deployed) {
			console.log("[deploy-demo-local] Using database storage fallback");
			try {
				const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
				const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
				const supabase = createClient(supabaseUrl, supabaseServiceKey);

				// Store the demo HTML in the database
				const { error: insertError } = await supabase
					.from('demo_html_storage')
					.insert({
						demo_id: demoId,
						assistant_id: assistantId,
						assistant_name: assistantName,
						assistant_type: assistantType,
						html_content: html,
						created_at: new Date().toISOString()
					});

				if (insertError) {
					console.error("[deploy-demo-local] Database storage failed:", insertError);
					throw new Error(`Database storage failed: ${insertError.message}`);
				}

				console.log("[deploy-demo-local] Demo stored in database successfully");
				finalDemoUrl = `https://ailabsafrica.com/demo-preview?id=${demoId}`;
				deployed = true;
			} catch (dbError) {
				console.error("[deploy-demo-local] Database fallback failed:", dbError);
				throw new Error(`Failed to deploy demo: ${(dbError as Error).message}`);
			}
		}

		// Send email notification
		const emailToSend = userEmail || guestEmail;
		if (emailToSend) {
			try {
				const Resend = await import("npm:resend@4.0.0");
				const resend = new Resend.Resend(Deno.env.get("RESEND_API_KEY") as string);
				await resend.emails.send({
					from: "AI Labs Africa <onboarding@resend.dev>",
					to: [emailToSend],
					subject: `Your AI Assistant Demo: ${assistantName}`,
					html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2 style="color: #333;">Your AI Assistant Demo is Ready! 🎉</h2>
              <p>Hello!</p>
              <p>Your AI assistant <strong>${assistantName}</strong> has been successfully created and deployed.</p>
              <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #495057;">Demo Details:</h3>
                <ul style="color: #6c757d;">
                  <li><strong>Assistant Name:</strong> ${assistantName}</li>
                  <li><strong>Type:</strong> ${assistantType.replace(/_/g, ' ')}</li>
                  <li><strong>Created:</strong> ${new Date().toLocaleDateString()}</li>
                </ul>
              </div>
                             <div style="text-align: center; margin: 30px 0;">
                 <a href="${finalDemoUrl}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                   🚀 View Your Demo
                 </a>
               </div>
               <p style="color: #6c757d; font-size: 14px;">
                 <strong>Demo URL:</strong> <a href="${finalDemoUrl}" style="color: #007bff;">${finalDemoUrl}</a>
               </p>
              ${guestEmail ? `
              <div style="background-color: #e7f3ff; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #007bff;">
                <p style="margin: 0; color: #0056b3; font-size: 14px;">
                  <strong>Guest Access:</strong> You can access all your assistants at any time by visiting 
                  <a href="https://ailabsafrica.com/guest-access" style="color: #007bff;">our guest access page</a> 
                  using your email and password.
                </p>
              </div>
              ` : ''}
              <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
              <p style="color: #6c757d; font-size: 12px; text-align: center;">
                This email was sent from AI Labs Africa. If you have any questions, please contact our support team.
              </p>
            </div>
          `,
				});
				console.log("[deploy-demo-local] Email sent successfully to:", emailToSend);
			} catch (emailError) {
				console.warn("[deploy-demo-local] Email send failed:", emailError?.message || emailError);
				// Don't throw error for email failure, continue with response
			}
		} else {
			console.log("[deploy-demo-local] No email address available for sending demo notification");
		}

		const response = {
			demo_url: finalDemoUrl,
			assistant_id: assistantId,
			demo_id: demoId,
			status: deployed ? "deployed" : "stored_in_db"
		};

		console.log("[deploy-demo-local] Deployment completed successfully:", response);

		return new Response(JSON.stringify(response), {
			headers: { ...corsHeaders, 'Content-Type': 'application/json' },
		});
	} catch (error) {
		console.error('[deploy-demo-local] Error:', error);
		console.error('[deploy-demo-local] Error stack:', error.stack);
		return new Response(JSON.stringify({ error: error.message }), {
			status: 500,
			headers: { ...corsHeaders, 'Content-Type': 'application/json' },
		});
	}
});
