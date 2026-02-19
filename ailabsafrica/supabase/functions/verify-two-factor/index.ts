import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { generateTOTP } from 'https://esm.sh/otplib@12.0.1'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface VerifyRequest {
	userId: string;
	code: string;
	secret: string;
}

serve(async (req) => {
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		const supabaseUrl = Deno.env.get('SUPABASE_URL')!
		const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
		const supabase = createClient(supabaseUrl, supabaseServiceKey)

		const { userId, code, secret }: VerifyRequest = await req.json()

		if (!userId || !code || !secret) {
			return new Response(
				JSON.stringify({ error: 'User ID, code, and secret are required' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Verify the TOTP code
		const currentCode = generateTOTP(secret)
		const isValid = currentCode === code

		if (!isValid) {
			return new Response(
				JSON.stringify({ error: 'Invalid verification code' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Enable 2FA in the database
		const { error: dbError } = await supabase
			.from('two_factor_auth')
			.update({
				is_enabled: true,
				enabled_at: new Date().toISOString()
			})
			.eq('user_id', userId)

		if (dbError) {
			console.error('Database error:', dbError)
			return new Response(
				JSON.stringify({ error: 'Failed to enable 2FA' }),
				{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: 'Two-factor authentication enabled successfully'
			}),
			{ status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)

	} catch (error) {
		console.error('Error in verify-two-factor:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}
})
