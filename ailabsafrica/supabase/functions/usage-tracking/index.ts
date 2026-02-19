import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		// Create Supabase client
		const supabaseClient = createClient(
			Deno.env.get('SUPABASE_URL') ?? '',
			Deno.env.get('SUPABASE_ANON_KEY') ?? '',
			{
				global: {
					headers: { Authorization: req.headers.get('Authorization')! },
				},
			}
		)

		// Parse the webhook payload
		const payload = await req.json()
		console.log('Usage tracking webhook received:', JSON.stringify(payload, null, 2))

		// Extract relevant information from the webhook
		const {
			event,
			call,
			assistant
		} = payload

		if (!event || !call || !assistant) {
			return new Response(
				JSON.stringify({ error: 'Invalid webhook payload' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Find the user who owns this assistant
		const { data: demoData, error: demoError } = await supabaseClient
			.from('custom_demos')
			.select('user_id, assistant_name')
			.eq('assistant_id', assistant.id)
			.single()

		if (demoError || !demoData) {
			console.error('Assistant not found in database:', assistant.id)
			return new Response(
				JSON.stringify({ error: 'Assistant not found' }),
				{
					status: 404,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		const userId = demoData.user_id
		const sessionId = call.id
		const assistantId = assistant.id

		// Handle different event types
		switch (event) {
			case 'call-started':
				// Create a new usage tracking record
				const { error: startError } = await supabaseClient
					.from('usage_tracking')
					.insert({
						user_id: userId,
						assistant_id: assistantId,
						session_id: sessionId,
						start_time: new Date().toISOString(),
						status: 'active',
						metadata: {
							call_id: call.id,
							assistant_name: demoData.assistant_name,
							event: event,
							call_data: call
						}
					})

				if (startError) {
					console.error('Error creating usage tracking record:', startError)
					return new Response(
						JSON.stringify({ error: 'Failed to create usage tracking' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				console.log(`Usage tracking started for session ${sessionId}`)
				break

			case 'call-ended':
				// Update the usage tracking record with end time and duration
				const startTime = new Date(call.startedAt || call.createdAt)
				const endTime = new Date(call.endedAt || new Date())
				const durationMinutes = (endTime.getTime() - startTime.getTime()) / (1000 * 60)
				const costPerMinute = 0.50
				const totalCost = durationMinutes * costPerMinute

				// Check if user has sufficient balance
				const { data: wallet, error: walletError } = await supabaseClient
					.from('wallets')
					.select('balance')
					.eq('user_id', userId)
					.single()

				if (walletError) {
					console.error('Error fetching wallet:', walletError)
					return new Response(
						JSON.stringify({ error: 'Failed to fetch wallet' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				if (wallet.balance < totalCost) {
					console.error(`Insufficient balance: ${wallet.balance} < ${totalCost}`)
					// Update usage record with insufficient balance status
					await supabaseClient
						.from('usage_tracking')
						.update({
							end_time: endTime.toISOString(),
							duration_minutes: durationMinutes,
							total_cost: totalCost,
							status: 'insufficient_balance',
							metadata: {
								...payload,
								insufficient_balance: true,
								required_balance: totalCost,
								available_balance: wallet.balance
							}
						})
						.eq('session_id', sessionId)

					return new Response(
						JSON.stringify({ error: 'Insufficient balance' }),
						{
							status: 402,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				// Deduct usage from wallet
				const { error: deductError } = await supabaseClient
					.rpc('deduct_usage_from_wallet', {
						p_user_id: userId,
						p_minutes: durationMinutes,
						p_assistant_id: assistantId,
						p_session_id: sessionId
					})

				if (deductError) {
					console.error('Error deducting usage:', deductError)
					return new Response(
						JSON.stringify({ error: 'Failed to deduct usage' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				// Update usage tracking record
				const { error: updateError } = await supabaseClient
					.from('usage_tracking')
					.update({
						end_time: endTime.toISOString(),
						duration_minutes: durationMinutes,
						total_cost: totalCost,
						status: 'completed',
						metadata: {
							...payload,
							duration_minutes: durationMinutes,
							total_cost: totalCost,
							cost_per_minute: costPerMinute
						}
					})
					.eq('session_id', sessionId)

				if (updateError) {
					console.error('Error updating usage tracking:', updateError)
				}

				console.log(`Usage tracking completed for session ${sessionId}: ${durationMinutes.toFixed(2)} minutes, $${totalCost.toFixed(2)}`)
				break

			case 'call-failed':
				// Mark the session as failed
				await supabaseClient
					.from('usage_tracking')
					.update({
						status: 'failed',
						metadata: {
							...payload,
							failure_reason: call.failureReason || 'Unknown failure'
						}
					})
					.eq('session_id', sessionId)

				console.log(`Usage tracking failed for session ${sessionId}`)
				break

			default:
				console.log(`Unhandled event type: ${event}`)
		}

		return new Response(
			JSON.stringify({ success: true, message: 'Usage tracking processed' }),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Unexpected error in usage tracking:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})
