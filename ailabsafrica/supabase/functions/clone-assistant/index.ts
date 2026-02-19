import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CloneAssistantRequest {
	source_assistant_id: string;
	new_name: string;
	user_id: string;
}

serve(async (req) => {
	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		// Create Supabase client
		const supabaseUrl = Deno.env.get('SUPABASE_URL')!
		const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
		const supabase = createClient(supabaseUrl, supabaseServiceKey)

		// Parse request body
		const { source_assistant_id, new_name, user_id }: CloneAssistantRequest = await req.json()

		if (!source_assistant_id || !new_name || !user_id) {
			return new Response(
				JSON.stringify({ error: 'Missing required fields: source_assistant_id, new_name, and user_id are required' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Verify user owns the source assistant
		const { data: sourceAssistant, error: sourceError } = await supabase
			.from('voice_agents')
			.select('*')
			.eq('id', source_assistant_id)
			.eq('user_id', user_id)
			.single()

		if (sourceError || !sourceAssistant) {
			return new Response(
				JSON.stringify({ error: 'Source assistant not found or access denied' }),
				{
					status: 404,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Check if the new name already exists for this user
		const { data: existingAssistant, error: existingError } = await supabase
			.from('voice_agents')
			.select('id')
			.eq('name', new_name)
			.eq('user_id', user_id)
			.eq('status', 'active')
			.single()

		if (existingAssistant) {
			return new Response(
				JSON.stringify({ error: 'An assistant with this name already exists' }),
				{
					status: 409,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Create new assistant in Vapi
		let newVapiAssistantId = null;
		const vapiSecretKey = Deno.env.get('VAPI_SECRET_KEY')

		if (vapiSecretKey && sourceAssistant.vapi_assistant_id) {
			try {
				// First, get the source assistant details from Vapi
				const vapiGetResponse = await fetch(`https://api.vapi.ai/assistant/${sourceAssistant.vapi_assistant_id}`, {
					method: 'GET',
					headers: {
						'Authorization': `Bearer ${vapiSecretKey}`,
						'Content-Type': 'application/json'
					}
				})

				if (vapiGetResponse.ok) {
					const sourceVapiAssistant = await vapiGetResponse.json()

					// Get webhook URL from environment
					const webhookUrl = Deno.env.get("VAPI_WEBHOOK_URL") || "https://ljzbzjgvwzivpmlmuxhx.supabase.co/functions/v1/vapi-webhook";
					const webhookSecret = Deno.env.get("VAPI_WEBHOOK_SECRET") || "8b4e9d5f6a93c7e124ff28dbd4a1c672b8f930ca9a7e55e8d3b42f7c93a61fd2";

					// Create new assistant with same configuration but new name
					const vapiCreateResponse = await fetch('https://api.vapi.ai/assistant', {
						method: 'POST',
						headers: {
							'Authorization': `Bearer ${vapiSecretKey}`,
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({
							name: new_name,
							model: sourceVapiAssistant.model || {
								provider: "openai",
								model: "gpt-4o-mini",
								messages: sourceVapiAssistant.model?.messages || []
							},
							voice: sourceVapiAssistant.voice || {
								provider: "vapi",
								voiceId: sourceAssistant.voice_id || "paige"
							},
							firstMessage: sourceVapiAssistant.firstMessage,
							recordingEnabled: sourceVapiAssistant.recordingEnabled !== undefined ? sourceVapiAssistant.recordingEnabled : false,
							endCallPhrases: sourceVapiAssistant.endCallPhrases || ["goodbye", "bye", "thank you"],
							// Configure webhook for real-time call events
							server: {
								url: webhookUrl,
								secret: webhookSecret
							},
							// Configure which server messages to receive
							serverMessages: [
								"call-start",
								"call-end",
								"end-of-call-report",
								"transcript",
								"conversation-update",
								"status-update",
								"function-call",
								"tool-calls",
								"hang",
								"speech-update",
								"transfer-destination-request",
								"handoff-destination-request",
								"user-interrupted"
							],
							metadata: {
								...sourceVapiAssistant.metadata,
								cloned_from: source_assistant_id,
								cloned_at: new Date().toISOString()
							}
						})
					})

					if (vapiCreateResponse.ok) {
						const newVapiAssistant = await vapiCreateResponse.json()
						newVapiAssistantId = newVapiAssistant.id
					} else {
						console.error('Failed to create assistant in Vapi:', await vapiCreateResponse.text())
					}
				} else {
					console.error('Failed to get source assistant from Vapi:', await vapiGetResponse.text())
				}
			} catch (vapiError) {
				console.error('Vapi cloning error:', vapiError)
				// Continue with database creation even if Vapi fails
			}
		}

		// Create new assistant in database
		const newAssistantData = {
			name: new_name,
			description: sourceAssistant.description,
			assistant_type: sourceAssistant.assistant_type,
			voice_id: sourceAssistant.voice_id,
			system_prompt: sourceAssistant.system_prompt,
			first_message: sourceAssistant.first_message,
			interrupt_threshold: sourceAssistant.interrupt_threshold,
			voice_sensitivity: sourceAssistant.voice_sensitivity,
			conversation_starters: sourceAssistant.conversation_starters,
			knowledge_base: sourceAssistant.knowledge_base,
			website_url: sourceAssistant.website_url,
			status: 'active',
			user_id: user_id,
			vapi_assistant_id: newVapiAssistantId,
			cloned_from: source_assistant_id,
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString()
		}

		const { data: newAssistant, error: createError } = await supabase
			.from('voice_agents')
			.insert([newAssistantData])
			.select()
			.single()

		if (createError) {
			console.error('Assistant creation error:', createError)
			return new Response(
				JSON.stringify({ error: 'Failed to create cloned assistant' }),
				{
					status: 500,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Create demo entry for the new assistant
		const demoData = {
			assistant_name: new_name,
			assistant_type: sourceAssistant.assistant_type,
			demo_url: `https://ai-labs-africa.vercel.app/demo-preview?id=${newAssistant.id}`,
			assistant_id: newAssistant.id,
			voice_id: sourceAssistant.voice_id,
			status: 'active',
			user_id: user_id,
			created_at: new Date().toISOString()
		}

		const { error: demoError } = await supabase
			.from('demos')
			.insert([demoData])

		if (demoError) {
			console.error('Demo creation error:', demoError)
			// Don't fail the request if demo creation fails
		}

		// Log the cloning action
		try {
			await supabase
				.from('assistant_actions')
				.insert([{
					assistant_id: newAssistant.id,
					user_id: user_id,
					action: 'clone',
					details: JSON.stringify({
						source_assistant_id: source_assistant_id,
						source_assistant_name: sourceAssistant.name,
						new_name: new_name
					}),
					created_at: new Date().toISOString()
				}])
		} catch (logError) {
			console.error('Failed to log assistant action:', logError)
			// Don't fail the request if logging fails
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: 'Assistant cloned successfully',
				assistant: newAssistant
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Clone assistant error:', error)
		return new Response(
			JSON.stringify({
				error: error instanceof Error ? error.message : 'Internal server error'
			}),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})
