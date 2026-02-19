import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ManageAssistantRequest {
	action: 'pause' | 'resume' | 'delete' | 'update' | 'status';
	assistant_id: string;
	user_id: string;
	status?: string;
	updates?: {
		name?: string;
		description?: string;
		instructions?: string;
		model?: string;
		voice_id?: string;
		first_message?: string;
		interrupt_threshold?: number;
		voice_sensitivity?: number;
		conversation_starters?: string[];
	};
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
		const { action, assistant_id, user_id, status, updates }: ManageAssistantRequest = await req.json()

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

		let updateData: any = {};

		switch (action) {
			case 'pause':
				updateData = {
					status: 'paused',
					updated_at: new Date().toISOString()
				};
				break;

			case 'resume':
				updateData = {
					status: 'active',
					updated_at: new Date().toISOString()
				};
				break;

			case 'status':
				if (!status) {
					return new Response(
						JSON.stringify({ error: 'Status is required for status action' }),
						{
							status: 400,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}
				updateData = {
					status: status,
					updated_at: new Date().toISOString()
				};
				break;

			case 'delete':
				// For delete action, we'll handle the actual deletion separately
				// This case is kept for backward compatibility but won't be used
				updateData = {
					status: 'deleted',
					deleted_at: new Date().toISOString(),
					updated_at: new Date().toISOString()
				};
				break;

			case 'update':
				if (!updates) {
					return new Response(
						JSON.stringify({ error: 'Updates object is required for update action' }),
						{
							status: 400,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				// Validate updates
				const allowedFields = [
					'name', 'description', 'instructions', 'model',
					'voice_id', 'first_message', 'interrupt_threshold',
					'voice_sensitivity', 'conversation_starters'
				];

				const validUpdates: any = {};
				Object.keys(updates).forEach(key => {
					if (allowedFields.includes(key)) {
						validUpdates[key] = updates[key as keyof typeof updates];
					}
				});

				updateData = {
					...validUpdates,
					updated_at: new Date().toISOString()
				};
				break;

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action. Use "pause", "resume", "delete", "update", or "status"' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
		}

		// Update assistant in database
		const { data: updatedAssistant, error: updateError } = await supabase
			.from('custom_demos')
			.update(updateData)
			.eq('id', assistant_id)
			.eq('user_id', user_id)
			.select()
			.single()

		if (updateError) {
			console.error('Assistant update error:', updateError)
			return new Response(
				JSON.stringify({ error: 'Failed to update assistant' }),
				{
					status: 500,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Update Vapi assistant if it exists and we're changing status
		if ((action === 'pause' || action === 'resume' || action === 'status') && assistant.assistant_id) {
			try {
				const vapiPrivateKey = Deno.env.get('VAPI_PRIVATE_KEY')
				if (vapiPrivateKey) {
					// Determine the new status for Vapi
					let vapiStatus = 'active';
					if (action === 'pause' || status === 'paused') {
						vapiStatus = 'paused';
					} else if (action === 'resume' || status === 'active') {
						vapiStatus = 'active';
					}

					// Call Vapi to update the assistant status
					const vapiResponse = await fetch(`https://api.vapi.ai/assistant/${assistant.assistant_id}`, {
						method: 'PATCH',
						headers: {
							'Authorization': `Bearer ${vapiPrivateKey}`,
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({
							enabled: vapiStatus === 'active'
						})
					})

					if (!vapiResponse.ok) {
						console.error('Failed to update assistant status in Vapi:', await vapiResponse.text())
					} else {
						console.log(`Successfully updated assistant ${assistant.assistant_id} status to ${vapiStatus} in Vapi`)
					}
				}
			} catch (vapiError) {
				console.error('Vapi status update error:', vapiError)
				// Don't fail the request if Vapi update fails
			}
		}

		// If action is delete, handle actual deletion
		if (action === 'delete') {
			// First, delete from Vapi if assistant exists there
			if (assistant.assistant_id) {
				try {
					const vapiPrivateKey = Deno.env.get('VAPI_PRIVATE_KEY')
					if (vapiPrivateKey) {
						console.log(`Deleting assistant ${assistant.assistant_id} from Vapi`)
						// Call Vapi to delete the assistant
						const vapiResponse = await fetch(`https://api.vapi.ai/assistant/${assistant.assistant_id}`, {
							method: 'DELETE',
							headers: {
								'Authorization': `Bearer ${vapiPrivateKey}`,
								'Content-Type': 'application/json'
							}
						})

						if (!vapiResponse.ok) {
							const errorText = await vapiResponse.text()
							console.error('Failed to delete assistant from Vapi:', errorText)
							throw new Error(`Vapi deletion failed: ${errorText}`)
						} else {
							console.log(`Successfully deleted assistant ${assistant.assistant_id} from Vapi`)
						}
					}
				} catch (vapiError) {
					console.error('Vapi deletion error:', vapiError)
					throw new Error(`Failed to delete from Vapi: ${vapiError.message}`)
				}
			}

			// Then, delete from database
			console.log(`Deleting assistant ${assistant_id} from database`)
			const { error: deleteError } = await supabase
				.from('custom_demos')
				.delete()
				.eq('id', assistant_id)
				.eq('user_id', user_id)

			if (deleteError) {
				console.error('Database deletion error:', deleteError)
				throw new Error(`Failed to delete from database: ${deleteError.message}`)
			}

			console.log(`Successfully deleted assistant ${assistant_id} from database`)

			// Return success response for deletion
			return new Response(
				JSON.stringify({
					success: true,
					message: 'Assistant deleted successfully from both Vapi and database'
				}),
				{
					status: 200,
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
					action: action,
					details: JSON.stringify(updateData),
					created_at: new Date().toISOString()
				}])
		} catch (logError) {
			console.error('Failed to log assistant action:', logError)
			// Don't fail the request if logging fails
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: `Assistant ${action}d successfully`,
				assistant: updatedAssistant
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Manage assistant error:', error)
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
