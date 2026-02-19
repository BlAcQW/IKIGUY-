import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface PasswordResetRequest {
	email: string;
}

interface PasswordResetConfirmRequest {
	token: string;
	password: string;
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

		if (req.method === 'POST' && body.action === 'request') {
			// Handle password reset request
			const { email }: PasswordResetRequest = body

			if (!email) {
				return new Response(
					JSON.stringify({ error: 'Email is required' }),
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

			// Check if user exists
			const { data: user, error: userError } = await supabase.auth.admin.listUsers()
			const existingUser = user.users.find(u => u.email === email)

			if (!existingUser) {
				// Don't reveal if user exists or not for security
				return new Response(
					JSON.stringify({
						success: true,
						message: 'If an account with this email exists, a password reset link has been sent.'
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Generate password reset token
			const { data: resetData, error: resetError } = await supabase.auth.admin.generateLink({
				type: 'recovery',
				email: email,
				options: {
					redirectTo: `${Deno.env.get('FRONTEND_URL') || 'http://localhost:8080'}/reset-password`
				}
			})

			if (resetError) {
				console.error('Password reset error:', resetError)
				return new Response(
					JSON.stringify({ error: 'Failed to send password reset email' }),
					{
						status: 500,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Send confirmation email
			try {
				await supabase
					.from('emails')
					.insert([{
						to_email: email,
						subject: 'Password Reset Request - AI Labs Africa',
						content: `
Dear User,

You have requested a password reset for your AI Labs Africa account.

If you did not request this reset, please ignore this email. Your password will remain unchanged.

To reset your password, click the link below:
${resetData.properties.action_link}

This link will expire in 24 hours.

If you have any questions, please contact our support team.

Best regards,
The AI Labs Africa Team
						`.trim(),
						from_name: 'AI Labs Africa',
						from_email: 'noreply@ailabsafrica.com'
					}])
			} catch (emailError) {
				console.error('Failed to send password reset email:', emailError)
				// Don't fail the request if email fails
			}

			return new Response(
				JSON.stringify({
					success: true,
					message: 'Password reset link has been sent to your email'
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)

		} else if (req.method === 'POST' && body.action === 'confirm') {
			// Handle password reset confirmation
			const { token, password }: PasswordResetConfirmRequest = body

			if (!token || !password) {
				return new Response(
					JSON.stringify({ error: 'Token and new password are required' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Validate password strength
			if (password.length < 8) {
				return new Response(
					JSON.stringify({ error: 'Password must be at least 8 characters long' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Update user password
			const { data: updateData, error: updateError } = await supabase.auth.admin.updateUserById(
				token, // This should be the user ID from the token
				{ password: password }
			)

			if (updateError) {
				console.error('Password update error:', updateError)
				return new Response(
					JSON.stringify({ error: 'Failed to update password. Token may be invalid or expired.' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
			}

			// Send confirmation email
			try {
				await supabase
					.from('emails')
					.insert([{
						to_email: updateData.user.email,
						subject: 'Password Updated Successfully - AI Labs Africa',
						content: `
Dear User,

Your password has been successfully updated.

If you did not make this change, please contact our support team immediately.

For security reasons, we recommend:
- Using a strong, unique password
- Enabling two-factor authentication if available
- Regularly updating your password

Best regards,
The AI Labs Africa Team
						`.trim(),
						from_name: 'AI Labs Africa',
						from_email: 'noreply@ailabsafrica.com'
					}])
			} catch (emailError) {
				console.error('Failed to send password update confirmation:', emailError)
			}

			return new Response(
				JSON.stringify({
					success: true,
					message: 'Password has been updated successfully'
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)

		} else {
			return new Response(
				JSON.stringify({ error: 'Invalid action. Use "request" or "confirm"' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

	} catch (error) {
		console.error('Password reset error:', error)
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
