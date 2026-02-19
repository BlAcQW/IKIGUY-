import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ManageConfigRequest {
	action: 'save' | 'get' | 'delete';
	assistant_id: string;
	user_id: string;
	configuration?: any;
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
		const { action, assistant_id, user_id, configuration }: ManageConfigRequest = await req.json()

		if (!action || !assistant_id || !user_id) {
			return new Response(
				JSON.stringify({ error: 'Missing required fields: action, assistant_id, and user_id are required' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Verify user owns the assistant
		const { data: assistant, error: assistantError } = await supabase
			.from('custom_demos')
			.select('*')
			.eq('id', assistant_id)
			.eq('user_id', user_id)
			.single()

		if (assistantError || !assistant) {
			return new Response(
				JSON.stringify({ error: 'Assistant not found or access denied' }),
				{
					status: 404,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		let result: any;

		switch (action) {
			case 'save':
				if (!configuration) {
					return new Response(
						JSON.stringify({ error: 'Configuration is required for save action' }),
						{
							status: 400,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				// Upsert configuration
				const { data: savedConfig, error: saveError } = await supabase
					.from('assistant_configurations')
					.upsert({
						assistant_id,
						user_id,
						configuration,
						updated_at: new Date().toISOString()
					}, {
						onConflict: 'assistant_id'
					})
					.select()
					.single()

				if (saveError) {
					console.error('Configuration save error:', saveError)
					return new Response(
						JSON.stringify({ error: 'Failed to save configuration' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				result = {
					success: true,
					message: 'Configuration saved successfully',
					configuration: savedConfig
				};
				break;

			case 'get':
				// Get configuration
				const { data: existingConfig, error: getError } = await supabase
					.from('assistant_configurations')
					.select('*')
					.eq('assistant_id', assistant_id)
					.eq('user_id', user_id)
					.single()

				if (getError && getError.code !== 'PGRST116') { // PGRST116 is "not found"
					console.error('Configuration get error:', getError)
					return new Response(
						JSON.stringify({ error: 'Failed to retrieve configuration' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				result = {
					success: true,
					message: 'Configuration retrieved successfully',
					configuration: existingConfig || { configuration: {} }
				};
				break;

			case 'delete':
				// Delete configuration
				const { error: deleteError } = await supabase
					.from('assistant_configurations')
					.delete()
					.eq('assistant_id', assistant_id)
					.eq('user_id', user_id)

				if (deleteError) {
					console.error('Configuration delete error:', deleteError)
					return new Response(
						JSON.stringify({ error: 'Failed to delete configuration' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				result = {
					success: true,
					message: 'Configuration deleted successfully'
				};
				break;

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action. Use "save", "get", or "delete"' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
		}

		// Log the action for analytics
		try {
			await supabase
				.from('assistant_actions')
				.insert([{
					assistant_id: assistant_id,
					user_id: user_id,
					action: `config_${action}`,
					details: JSON.stringify({ action, configuration }),
					created_at: new Date().toISOString()
				}])
		} catch (logError) {
			console.error('Failed to log assistant action:', logError)
			// Don't fail the request if logging fails
		}

		return new Response(
			JSON.stringify(result),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Manage assistant config error:', error)
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
