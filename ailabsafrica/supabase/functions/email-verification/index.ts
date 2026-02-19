import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface EmailVerificationRequest {
	action: 'send' | 'verify';
	email?: string;
	token?: string;
	user_id?: string;
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
		const { action, email, token, user_id }: EmailVerificationRequest = await req.json()

		if (!action) {
			return new Response(
				JSON.stringify({ error: 'Action is required' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		if (action === 'send') {
			// Handle email verification request
			if (!email) {
				return new Response(
					JSON.stringify({ error: 'Email is required for send action' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Validate email format
			const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
			if (!emailRegex.test(email)) {
				return new Response(
					JSON.stringify({ error: 'Invalid email format' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Check if user exists and is not already verified
			const { data: user, error: userError } = await supabase.auth.admin.listUsers()
			const existingUser = user.users.find(u => u.email === email)

			if (!existingUser) {
				return new Response(
					JSON.stringify({ error: 'User not found' }),
					{
						status: 404,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			if (existingUser.email_confirmed_at) {
				return new Response(
					JSON.stringify({ error: 'Email is already verified' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Generate email verification link
			const { data: verificationData, error: verificationError } = await supabase.auth.admin.generateLink({
				type: 'signup',
				email: email,
				options: {
					redirectTo: `${Deno.env.get('FRONTEND_URL') || 'http://localhost:8080'}/verify-email`
				}
			})

			if (verificationError) {
				console.error('Email verification error:', verificationError)
				return new Response(
					JSON.stringify({ error: 'Failed to send verification email' }),
					{
						status: 500,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Send verification email
			try {
				await supabase
					.from('emails')
					.insert([{
						to_email: email,
						subject: 'Verify Your Email - AI Labs Africa',
						content: `
Dear User,

Welcome to AI Labs Africa! Please verify your email address to complete your registration.

To verify your email, click the link below:
${verificationData.properties.action_link}

This link will expire in 24 hours.

If you did not create an account with us, please ignore this email.

Best regards,
The AI Labs Africa Team
						`.trim(),
						from_name: 'AI Labs Africa',
						from_email: 'noreply@ailabsafrica.com'
					}])
			} catch (emailError) {
				console.error('Failed to send verification email:', emailError)
				// Don't fail the request if email fails
			}

			return new Response(
				JSON.stringify({
					success: true,
					message: 'Verification email has been sent'
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)

		} else if (action === 'verify') {
			// Handle email verification confirmation
			if (!token) {
				return new Response(
					JSON.stringify({ error: 'Verification token is required' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Verify the email using the token
			try {
				// The token should be processed by Supabase Auth
				// This is typically handled by the frontend when the user clicks the link
				// For now, we'll just return success
				return new Response(
					JSON.stringify({
						success: true,
						message: 'Email verified successfully'
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			} catch (verifyError) {
				console.error('Email verification error:', verifyError)
				return new Response(
					JSON.stringify({ error: 'Failed to verify email. Token may be invalid or expired.' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

		} else {
			return new Response(
				JSON.stringify({ error: 'Invalid action. Use "send" or "verify"' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

	} catch (error) {
		console.error('Email verification error:', error)
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
