import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CreateVersionRequest {
	demo_id: string;
	version_notes?: string;
}

interface RollbackVersionRequest {
	demo_id: string;
	version_number: number;
}

interface GetVersionHistoryRequest {
	demo_id: string;
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

		// Get the action from the URL
		const url = new URL(req.url)
		const action = url.searchParams.get('action')

		// Get the request body
		const requestBody = await req.json()

		switch (action) {
			case 'create_version':
				return await handleCreateVersion(supabase, requestBody as CreateVersionRequest)

			case 'rollback_version':
				return await handleRollbackVersion(supabase, requestBody as RollbackVersionRequest)

			case 'get_version_history':
				return await handleGetVersionHistory(supabase, requestBody as GetVersionHistoryRequest)

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
		}
	} catch (error) {
		console.error('Error in demo-versioning function:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})

async function handleCreateVersion(supabase: any, request: CreateVersionRequest) {
	const { demo_id, version_notes } = request

	if (!demo_id) {
		return new Response(
			JSON.stringify({ error: 'demo_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Call the database function to create a new version
		const { data, error } = await supabase.rpc('create_demo_version', {
			p_demo_id: demo_id,
			p_version_notes: version_notes || null
		})

		if (error) {
			console.error('Error creating demo version:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				version_number: data,
				message: `Version ${data} created successfully`
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleCreateVersion:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to create version' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleRollbackVersion(supabase: any, request: RollbackVersionRequest) {
	const { demo_id, version_number } = request

	if (!demo_id || !version_number) {
		return new Response(
			JSON.stringify({ error: 'demo_id and version_number are required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Call the database function to rollback to the specified version
		const { data, error } = await supabase.rpc('rollback_demo_version', {
			p_demo_id: demo_id,
			p_version_number: version_number
		})

		if (error) {
			console.error('Error rolling back demo version:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: `Successfully rolled back to version ${version_number}`
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleRollbackVersion:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to rollback version' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleGetVersionHistory(supabase: any, request: GetVersionHistoryRequest) {
	const { demo_id } = request

	if (!demo_id) {
		return new Response(
			JSON.stringify({ error: 'demo_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Call the database function to get version history
		const { data, error } = await supabase.rpc('get_demo_version_history', {
			p_demo_id: demo_id
		})

		if (error) {
			console.error('Error getting demo version history:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				versions: data || []
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleGetVersionHistory:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to get version history' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}
