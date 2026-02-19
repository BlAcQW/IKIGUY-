import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { generateSecret, generateTOTP, generateQRCode } from 'https://esm.sh/otplib@12.0.1'
import { generateBackupCodes } from './utils.ts'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface SetupRequest {
	userId: string;
}

serve(async (req) => {
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		const supabaseUrl = Deno.env.get('SUPABASE_URL')!
		const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
		const supabase = createClient(supabaseUrl, supabaseServiceKey)

		const { userId }: SetupRequest = await req.json()

		if (!userId) {
			return new Response(
				JSON.stringify({ error: 'User ID is required' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Generate a new TOTP secret
		const secret = generateSecret()

		// Generate backup codes
		const backupCodes = generateBackupCodes()

		// Create QR code URL for authenticator apps
		const appName = 'AI Labs Africa'
		const accountName = userId // You might want to use user's email instead
		const qrCodeUrl = `otpauth://totp/${encodeURIComponent(appName)}:${encodeURIComponent(accountName)}?secret=${secret}&issuer=${encodeURIComponent(appName)}`

		// Generate QR code image
		const qrCode = await generateQRCode(qrCodeUrl)

		// Store the secret and backup codes in the database (encrypted)
		const { error: dbError } = await supabase
			.from('two_factor_auth')
			.upsert([{
				user_id: userId,
				secret: secret, // In production, this should be encrypted
				backup_codes: backupCodes,
				is_enabled: false,
				created_at: new Date().toISOString()
			}])

		if (dbError) {
			console.error('Database error:', dbError)
			return new Response(
				JSON.stringify({ error: 'Failed to store 2FA setup' }),
				{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				secret: secret,
				qrCode: qrCode,
				backupCodes: backupCodes,
				message: '2FA setup generated successfully'
			}),
			{ status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)

	} catch (error) {
		console.error('Error in setup-two-factor:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}
})
