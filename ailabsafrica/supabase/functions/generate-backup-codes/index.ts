import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { generateBackupCodes } from '../setup-two-factor/utils.ts'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface BackupCodesRequest {
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

		const { userId }: BackupCodesRequest = await req.json()

		if (!userId) {
			return new Response(
				JSON.stringify({ error: 'User ID is required' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Generate new backup codes
		const newBackupCodes = generateBackupCodes()

		// Update the backup codes in the database
		const { error: dbError } = await supabase
			.from('two_factor_auth')
			.update({
				backup_codes: newBackupCodes,
				updated_at: new Date().toISOString()
			})
			.eq('user_id', userId)

		if (dbError) {
			console.error('Database error:', dbError)
			return new Response(
				JSON.stringify({ error: 'Failed to update backup codes' }),
				{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				backupCodes: newBackupCodes,
				message: 'New backup codes generated successfully'
			}),
			{ status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)

	} catch (error) {
		console.error('Error in generate-backup-codes:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}
})
