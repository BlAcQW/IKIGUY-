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

		// Get the user from the request
		const {
			data: { user },
			error: authError,
		} = await supabaseClient.auth.getUser()

		if (authError || !user) {
			return new Response(
				JSON.stringify({ error: 'Unauthorized' }),
				{
					status: 401,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Parse request body
		const { bundleId, amount, minutes } = await req.json()

		if (!bundleId || !amount || !minutes) {
			return new Response(
				JSON.stringify({ error: 'Missing required fields: bundleId, amount, minutes' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Verify the bundle exists and is active
		const { data: bundle, error: bundleError } = await supabaseClient
			.from('usage_bundles')
			.select('*')
			.eq('id', bundleId)
			.eq('is_active', true)
			.single()

		if (bundleError || !bundle) {
			return new Response(
				JSON.stringify({ error: 'Bundle not found or inactive' }),
				{
					status: 404,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Verify the bundle matches the provided details
		if (bundle.price !== amount || bundle.minutes !== minutes) {
			return new Response(
				JSON.stringify({ error: 'Bundle details mismatch' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Process the purchase using the database function
		const { data: result, error: purchaseError } = await supabaseClient
			.rpc('add_minutes_to_wallet', {
				p_user_id: user.id,
				p_minutes: minutes,
				p_amount: amount,
				p_bundle_id: bundleId
			})

		if (purchaseError) {
			console.error('Purchase error:', purchaseError)
			return new Response(
				JSON.stringify({ error: purchaseError.message }),
				{
					status: 500,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Get updated wallet balance
		const { data: wallet, error: walletError } = await supabaseClient
			.from('wallets')
			.select('balance')
			.eq('user_id', user.id)
			.single()

		if (walletError) {
			console.error('Wallet fetch error:', walletError)
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: `Successfully purchased ${minutes} minutes for $${amount}`,
				bundle: {
					id: bundle.id,
					name: bundle.name,
					minutes: bundle.minutes,
					price: bundle.price
				},
				wallet_balance: wallet?.balance || 0
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Unexpected error:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})
