import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TrackAnalyticsRequest {
	demo_id: string;
	assistant_id: string;
	event_type: 'view' | 'interaction' | 'conversion' | 'share' | 'embed';
	session_id: string;
	event_data?: any;
	user_agent?: string;
	ip_address?: string;
	referrer?: string;
	page_url?: string;
	duration_seconds?: number;
}

interface SessionRequest {
	demo_id: string;
	assistant_id: string;
	session_id: string;
	action: 'start' | 'end' | 'update';
	user_agent?: string;
	ip_address?: string;
	referrer?: string;
	interaction_count?: number;
	conversion_events?: any[];
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
		const body = await req.json()
		const { action } = body

		if (action === 'track_event') {
			const {
				demo_id,
				assistant_id,
				event_type,
				session_id,
				event_data,
				user_agent,
				ip_address,
				referrer,
				page_url,
				duration_seconds
			}: TrackAnalyticsRequest = body

			if (!demo_id || !assistant_id || !event_type || !session_id) {
				return new Response(
					JSON.stringify({ error: 'Missing required fields: demo_id, assistant_id, event_type, and session_id are required' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Verify demo exists
			const { data: demo, error: demoError } = await supabase
				.from('custom_demos')
				.select('id')
				.eq('id', demo_id)
				.single()

			if (demoError || !demo) {
				return new Response(
					JSON.stringify({ error: 'Demo not found' }),
					{
						status: 404,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Insert analytics event
			const { data: analyticsEvent, error: analyticsError } = await supabase
				.from('demo_analytics')
				.insert([{
					demo_id,
					assistant_id,
					session_id,
					event_type,
					event_data: event_data || null,
					user_agent: user_agent || null,
					ip_address: ip_address || null,
					referrer: referrer || null,
					page_url: page_url || null,
					duration_seconds: duration_seconds || null,
					created_at: new Date().toISOString()
				}])
				.select()
				.single()

			if (analyticsError) {
				console.error('Analytics event insertion error:', analyticsError)
				return new Response(
					JSON.stringify({ error: 'Failed to track analytics event' }),
					{
						status: 500,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			return new Response(
				JSON.stringify({
					success: true,
					message: 'Analytics event tracked successfully',
					event: analyticsEvent
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)

		} else if (action === 'session') {
			const {
				demo_id,
				assistant_id,
				session_id,
				action: sessionAction,
				user_agent,
				ip_address,
				referrer,
				interaction_count,
				conversion_events
			}: SessionRequest = body

			if (!demo_id || !assistant_id || !session_id || !sessionAction) {
				return new Response(
					JSON.stringify({ error: 'Missing required fields: demo_id, assistant_id, session_id, and action are required' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Verify demo exists
			const { data: demo, error: demoError } = await supabase
				.from('custom_demos')
				.select('id')
				.eq('id', demo_id)
				.single()

			if (demoError || !demo) {
				return new Response(
					JSON.stringify({ error: 'Demo not found' }),
					{
						status: 404,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			if (sessionAction === 'start') {
				// Start new session
				const { data: session, error: sessionError } = await supabase
					.from('demo_sessions')
					.insert([{
						session_id,
						demo_id,
						assistant_id,
						user_agent: user_agent || null,
						ip_address: ip_address || null,
						referrer: referrer || null,
						started_at: new Date().toISOString()
					}])
					.select()
					.single()

				if (sessionError) {
					console.error('Session creation error:', sessionError)
					return new Response(
						JSON.stringify({ error: 'Failed to create session' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				return new Response(
					JSON.stringify({
						success: true,
						message: 'Session started successfully',
						session
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)

			} else if (sessionAction === 'end' || sessionAction === 'update') {
				// Update existing session
				const updateData: any = {}

				if (sessionAction === 'end') {
					updateData.ended_at = new Date().toISOString()
					// Calculate duration
					const { data: session } = await supabase
						.from('demo_sessions')
						.select('started_at')
						.eq('session_id', session_id)
						.single()

					if (session?.started_at) {
						const startTime = new Date(session.started_at)
						const endTime = new Date()
						updateData.duration_seconds = Math.floor((endTime.getTime() - startTime.getTime()) / 1000)
					}
				}

				if (interaction_count !== undefined) {
					updateData.interaction_count = interaction_count
				}

				if (conversion_events !== undefined) {
					updateData.conversion_events = conversion_events
				}

				const { data: updatedSession, error: updateError } = await supabase
					.from('demo_sessions')
					.update(updateData)
					.eq('session_id', session_id)
					.select()
					.single()

				if (updateError) {
					console.error('Session update error:', updateError)
					return new Response(
						JSON.stringify({ error: 'Failed to update session' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				return new Response(
					JSON.stringify({
						success: true,
						message: `Session ${sessionAction === 'end' ? 'ended' : 'updated'} successfully`,
						session: updatedSession
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

		} else {
			return new Response(
				JSON.stringify({ error: 'Invalid action. Use "track_event" or "session"' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

	} catch (error) {
		console.error('Track demo analytics error:', error)
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
