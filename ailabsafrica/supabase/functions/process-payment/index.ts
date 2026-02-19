import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface PaymentRequest {
	amount: number;
	currency: string;
	payment_method: string;
	transaction_id: string;
	email?: string;
	phone?: string;
	name?: string;
}

interface FlutterwaveResponse {
	status: string;
	message: string;
	data: {
		link: string;
		reference: string;
	};
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

		// Get Flutterwave secret key
		const flutterwaveSecretKey = Deno.env.get('FLUTTERWAVE_SECRET_KEY')
		if (!flutterwaveSecretKey) {
			throw new Error('Flutterwave secret key not configured')
		}

		// Parse request body
		const { amount, currency, payment_method, transaction_id, email, phone, name }: PaymentRequest = await req.json()

		// Validate required fields
		if (!amount || !currency || !payment_method || !transaction_id) {
			return new Response(
				JSON.stringify({
					error: 'Missing required fields: amount, currency, payment_method, and transaction_id are required'
				}),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Validate amount
		if (amount <= 0) {
			return new Response(
				JSON.stringify({ error: 'Amount must be greater than 0' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Prepare Flutterwave payment data
		const paymentData = {
			tx_ref: transaction_id,
			amount: amount.toString(),
			currency: currency.toUpperCase(),
			redirect_url: `${Deno.env.get('FRONTEND_URL') || 'http://localhost:8080'}/payment-success?tx_ref=${transaction_id}`,
			customer: {
				email: email || 'customer@example.com',
				phone_number: phone || '',
				name: name || 'Customer'
			},
			customizations: {
				title: 'AI Labs Africa - Wallet Top Up',
				description: `Wallet top up of ${currency} ${amount}`,
				logo: 'https://ailabsafrica.com/logo.png'
			},
			meta: {
				transaction_id,
				payment_method
			}
		}

		// Initialize Flutterwave payment
		const flutterwaveResponse = await fetch('https://api.flutterwave.com/v3/payments', {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${flutterwaveSecretKey}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(paymentData)
		})

		const flutterwaveResult: FlutterwaveResponse = await flutterwaveResponse.json()

		if (flutterwaveResult.status !== 'success') {
			throw new Error(flutterwaveResult.message || 'Failed to initialize payment')
		}

		// Update transaction status in database
		const { error: updateError } = await supabase
			.from('payment_transactions')
			.update({
				status: 'pending',
				payment_reference: flutterwaveResult.data.reference,
				payment_link: flutterwaveResult.data.link,
				updated_at: new Date().toISOString()
			})
			.eq('transaction_id', transaction_id)

		if (updateError) {
			console.error('Database update error:', updateError)
			// Don't fail the request, just log the error
		}

		return new Response(
			JSON.stringify({
				success: true,
				payment_url: flutterwaveResult.data.link,
				reference: flutterwaveResult.data.reference,
				message: 'Payment initialized successfully'
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Payment processing error:', error)
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