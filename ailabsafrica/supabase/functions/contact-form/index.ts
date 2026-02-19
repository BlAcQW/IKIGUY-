import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ContactFormData {
	name: string;
	email: string;
	company: string;
	phone: string;
	subject: string;
	message: string;
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
		const { name, email, company, phone, subject, message }: ContactFormData = await req.json()

		// Validate required fields
		if (!name || !email || !subject || !message) {
			return new Response(
				JSON.stringify({
					error: 'Missing required fields: name, email, subject, and message are required'
				}),
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

		// Store contact form submission in database
		const { error: dbError } = await supabase
			.from('contact_submissions')
			.insert([
				{
					name,
					email,
					company: company || null,
					phone: phone || null,
					subject,
					message,
					status: 'new'
				}
			])

		if (dbError) {
			console.error('Database error:', dbError)
			return new Response(
				JSON.stringify({ error: 'Failed to save contact form submission' }),
				{
					status: 500,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Send email notification (using Supabase's built-in email service)
		const emailContent = `
New Contact Form Submission

Name: ${name}
Email: ${email}
Company: ${company || 'Not provided'}
Phone: ${phone || 'Not provided'}
Subject: ${subject}

Message:
${message}

---
This message was sent from the AI Labs Africa contact form.
    `.trim()

		const { error: emailError } = await supabase
			.from('emails')
			.insert([
				{
					to: 'alfred.anyan@gmail.com',
					subject: `New Contact Form: ${subject}`,
					content: emailContent,
					from_name: name,
					from_email: email
				}
			])

		if (emailError) {
			console.error('Email error:', emailError)
			// Don't fail the request if email fails, just log it
		}

		// Send confirmation email to user
		const confirmationContent = `
Dear ${name},

Thank you for contacting AI Labs Africa. We have received your message and will get back to you within 24 hours.

Your message details:
Subject: ${subject}
Message: ${message}

If you have any urgent questions, please call us at +233 54 569 9663.

Best regards,
The AI Labs Africa Team
    `.trim()

		const { error: confirmationError } = await supabase
			.from('emails')
			.insert([
				{
					to: email,
					subject: 'Thank you for contacting AI Labs Africa',
					content: confirmationContent,
					from_name: 'AI Labs Africa',
					from_email: 'noreply@ailabsafrica.com'
				}
			])

		if (confirmationError) {
			console.error('Confirmation email error:', confirmationError)
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: 'Contact form submitted successfully'
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Contact form error:', error)
		return new Response(
			JSON.stringify({
				error: 'Internal server error'
			}),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})
