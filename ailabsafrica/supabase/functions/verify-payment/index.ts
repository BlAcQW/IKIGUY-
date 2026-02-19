import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface VerificationRequest {
	tx_ref: string;
}

interface FlutterwaveVerificationResponse {
	status: string;
	message: string;
	data: {
		id: number;
		tx_ref: string;
		flw_ref: string;
		device_fingerprint: string;
		amount: number;
		currency: string;
		charged_amount: number;
		app_fee: number;
		merchant_fee: number;
		processor_response: string;
		auth_model: string;
		ip: string;
		narration: string;
		status: string;
		payment_type: string;
		created_at: string;
		account_id: number;
		customer: {
			id: number;
			name: string;
			phone_number: string;
			email: string;
			created_at: string;
		};
		meta: {
			transaction_id: string;
			payment_method: string;
		};
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
		const { tx_ref }: VerificationRequest = await req.json()

		if (!tx_ref) {
			return new Response(
				JSON.stringify({ error: 'Transaction reference is required' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Verify payment with Flutterwave
		const verificationResponse = await fetch(`https://api.flutterwave.com/v3/transactions/${tx_ref}/verify`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${flutterwaveSecretKey}`,
				'Content-Type': 'application/json'
			}
		})

		const verificationResult: FlutterwaveVerificationResponse = await verificationResponse.json()

		if (verificationResult.status !== 'success') {
			throw new Error(verificationResult.message || 'Payment verification failed')
		}

		const paymentData = verificationResult.data
		const transactionId = paymentData.meta?.transaction_id || tx_ref

		// Check if payment is successful
		if (paymentData.status !== 'successful') {
			// Update transaction status to failed
			await supabase
				.from('payment_transactions')
				.update({
					status: 'failed',
					provider_response: paymentData,
					updated_at: new Date().toISOString()
				})
				.eq('transaction_id', transactionId)

			return new Response(
				JSON.stringify({
					success: false,
					error: `Payment ${paymentData.status}`,
					amount: paymentData.amount
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Get transaction details from database
		const { data: transaction, error: transactionError } = await supabase
			.from('payment_transactions')
			.select('*')
			.eq('transaction_id', transactionId)
			.single()

		if (transactionError || !transaction) {
			throw new Error('Transaction not found in database')
		}

		// Check if already processed
		if (transaction.status === 'completed') {
			return new Response(
				JSON.stringify({
					success: true,
					message: 'Payment already processed',
					amount: paymentData.amount
				}),
				{
					status: 200,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Update transaction status to completed
		const { error: updateError } = await supabase
			.from('payment_transactions')
			.update({
				status: 'completed',
				provider_response: paymentData,
				completed_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			})
			.eq('transaction_id', transactionId)

		if (updateError) {
			throw new Error('Failed to update transaction status')
		}

		// Update wallet balance
		const { data: wallet, error: walletError } = await supabase
			.from('wallets')
			.select('balance')
			.eq('user_id', transaction.user_id)
			.single()

		if (walletError) {
			// Create wallet if it doesn't exist
			const { error: createError } = await supabase
				.from('wallets')
				.insert([{
					user_id: transaction.user_id,
					balance: paymentData.amount,
					currency: paymentData.currency
				}])

			if (createError) {
				throw new Error('Failed to create wallet')
			}
		} else {
			// Update existing wallet
			const newBalance = (wallet.balance || 0) + paymentData.amount
			const { error: balanceError } = await supabase
				.from('wallets')
				.update({
					balance: newBalance,
					updated_at: new Date().toISOString()
				})
				.eq('user_id', transaction.user_id)

			if (balanceError) {
				throw new Error('Failed to update wallet balance')
			}
		}

		// Send confirmation email
		try {
			const { data: user } = await supabase.auth.admin.getUserById(transaction.user_id)
			if (user?.user?.email) {
				await supabase
					.from('emails')
					.insert([{
						to_email: user.user.email,
						subject: 'Payment Successful - AI Labs Africa',
						content: `
Dear ${user.user.email},

Your payment of ${paymentData.currency} ${paymentData.amount} has been successfully processed.

Transaction Details:
- Transaction ID: ${transactionId}
- Amount: ${paymentData.currency} ${paymentData.amount}
- Payment Method: ${paymentData.payment_type}
- Date: ${new Date().toLocaleString()}

Your wallet has been credited and you can now use our AI services.

Thank you for choosing AI Labs Africa!

Best regards,
The AI Labs Africa Team
            `.trim(),
						from_name: 'AI Labs Africa',
						from_email: 'noreply@ailabsafrica.com'
					}])
			}
		} catch (emailError) {
			console.error('Failed to send confirmation email:', emailError)
			// Don't fail the request if email fails
		}

		return new Response(
			JSON.stringify({
				success: true,
				message: 'Payment verified and wallet updated successfully',
				amount: paymentData.amount,
				currency: paymentData.currency
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Payment verification error:', error)
		return new Response(
			JSON.stringify({
				success: false,
				error: error instanceof Error ? error.message : 'Internal server error'
			}),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})