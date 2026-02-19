import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface RefundRequest {
	transaction_id: string;
	amount?: number; // Optional: partial refund amount
	reason: string;
	user_id: string;
}

interface FlutterwaveRefundResponse {
	status: string;
	message: string;
	data: {
		id: number;
		amount: number;
		currency: string;
		flw_ref: string;
		tx_ref: string;
		status: string;
		created_at: string;
	};
}

serve(async (req) => {
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		const supabaseUrl = Deno.env.get('SUPABASE_URL')!
		const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
		const supabase = createClient(supabaseUrl, supabaseServiceKey)

		const flutterwaveSecretKey = Deno.env.get('FLUTTERWAVE_SECRET_KEY')
		if (!flutterwaveSecretKey) {
			throw new Error('Flutterwave secret key not configured')
		}

		const { transaction_id, amount, reason, user_id }: RefundRequest = await req.json()

		if (!transaction_id || !reason || !user_id) {
			return new Response(
				JSON.stringify({ error: 'Transaction ID, reason, and user ID are required' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Get the original transaction details
		const { data: transaction, error: transactionError } = await supabase
			.from('payment_transactions')
			.select('*')
			.eq('transaction_id', transaction_id)
			.eq('user_id', user_id)
			.single()

		if (transactionError || !transaction) {
			return new Response(
				JSON.stringify({ error: 'Transaction not found' }),
				{ status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Check if transaction is eligible for refund
		if (transaction.status !== 'successful') {
			return new Response(
				JSON.stringify({ error: 'Transaction is not eligible for refund' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Check if refund amount is valid
		const refundAmount = amount || transaction.amount
		if (refundAmount > transaction.amount) {
			return new Response(
				JSON.stringify({ error: 'Refund amount cannot exceed original transaction amount' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Check if transaction has already been refunded
		const { data: existingRefund } = await supabase
			.from('refunds')
			.select('*')
			.eq('transaction_id', transaction_id)
			.eq('status', 'successful')

		if (existingRefund && existingRefund.length > 0) {
			return new Response(
				JSON.stringify({ error: 'Transaction has already been refunded' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Create refund record in database
		const { data: refundRecord, error: refundError } = await supabase
			.from('refunds')
			.insert([{
				transaction_id: transaction_id,
				user_id: user_id,
				amount: refundAmount,
				currency: transaction.currency,
				reason: reason,
				status: 'pending',
				refund_type: amount ? 'partial' : 'full',
				created_at: new Date().toISOString()
			}])
			.select()
			.single()

		if (refundError) {
			console.error('Error creating refund record:', refundError)
			return new Response(
				JSON.stringify({ error: 'Failed to create refund record' }),
				{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Process refund through Flutterwave
		const refundData = {
			flw_ref: transaction.flw_ref || transaction_id,
			amount: refundAmount.toString(),
			reason: reason
		}

		const flutterwaveResponse = await fetch('https://api.flutterwave.com/v3/refunds', {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${flutterwaveSecretKey}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(refundData)
		})

		const refundResult: FlutterwaveRefundResponse = await flutterwaveResponse.json()

		if (refundResult.status !== 'success') {
			// Update refund status to failed
			await supabase
				.from('refunds')
				.update({
					status: 'failed',
					error_message: refundResult.message,
					updated_at: new Date().toISOString()
				})
				.eq('id', refundRecord.id)

			return new Response(
				JSON.stringify({ error: refundResult.message || 'Refund processing failed' }),
				{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		// Update refund record with success
		await supabase
			.from('refunds')
			.update({
				status: 'successful',
				flw_refund_id: refundResult.data.id.toString(),
				processed_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			})
			.eq('id', refundRecord.id)

		// Update wallet balance (deduct the refunded amount)
		const { data: wallet } = await supabase
			.from('wallets')
			.select('balance')
			.eq('user_id', user_id)
			.single()

		if (wallet) {
			const newBalance = Math.max(0, wallet.balance - refundAmount)
			await supabase
				.from('wallets')
				.update({
					balance: newBalance,
					updated_at: new Date().toISOString()
				})
				.eq('user_id', user_id)
		}

		// Update transaction status if full refund
		if (!amount || amount === transaction.amount) {
			await supabase
				.from('payment_transactions')
				.update({
					status: 'refunded',
					updated_at: new Date().toISOString()
				})
				.eq('transaction_id', transaction_id)
		}

		return new Response(
			JSON.stringify({
				success: true,
				refund_id: refundRecord.id,
				amount: refundAmount,
				currency: transaction.currency,
				status: 'successful',
				message: 'Refund processed successfully'
			}),
			{ status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)

	} catch (error) {
		console.error('Error in process-refund:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}
})
