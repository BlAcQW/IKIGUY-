import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface InvoiceRequest {
	invoiceData: {
		invoiceNumber: string;
		date: string;
		dueDate: string;
		customer: {
			name: string;
			email: string;
			phone?: string;
			company?: string;
		};
		items: Array<{
			description: string;
			quantity: number;
			unitPrice: number;
			amount: number;
		}>;
		subtotal: number;
		tax: number;
		total: number;
		status: string;
	};
	transactionId: string;
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
		const { invoiceData, transactionId }: InvoiceRequest = await req.json()

		// Validate required fields
		if (!invoiceData || !transactionId) {
			return new Response(
				JSON.stringify({
					error: 'Missing required fields: invoiceData and transactionId are required'
				}),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Generate PDF using a PDF generation service
		// For this example, we'll use a simple HTML to PDF conversion
		// In production, you might want to use a service like Puppeteer, jsPDF, or a cloud service

		const pdfHtml = `
			<!DOCTYPE html>
			<html>
				<head>
					<title>Invoice ${invoiceData.invoiceNumber}</title>
					<style>
						body { 
							font-family: Arial, sans-serif; 
							margin: 40px; 
							color: #333;
							line-height: 1.6;
						}
						.header { 
							text-align: center; 
							margin-bottom: 40px; 
							border-bottom: 2px solid #2563eb;
							padding-bottom: 20px;
						}
						.header h1 { 
							color: #2563eb; 
							margin: 0; 
							font-size: 28px;
						}
						.header h2 { 
							color: #64748b; 
							margin: 10px 0 0 0;
							font-size: 18px;
						}
						.invoice-details { 
							margin-bottom: 30px; 
							display: flex;
							justify-content: space-between;
						}
						.customer-details { 
							margin-bottom: 30px; 
						}
						.customer-details h3 {
							color: #2563eb;
							margin-bottom: 10px;
						}
						table { 
							width: 100%; 
							border-collapse: collapse; 
							margin-bottom: 30px; 
						}
						th, td { 
							border: 1px solid #e2e8f0; 
							padding: 12px; 
							text-align: left; 
						}
						th { 
							background-color: #f8fafc; 
							font-weight: 600;
							color: #475569;
						}
						.total { 
							text-align: right; 
							font-weight: bold; 
							font-size: 16px;
						}
						.total p {
							margin: 5px 0;
						}
						.footer {
							margin-top: 50px;
							text-align: center;
							color: #64748b;
							border-top: 1px solid #e2e8f0;
							padding-top: 20px;
						}
						.status-badge {
							display: inline-block;
							padding: 4px 12px;
							border-radius: 20px;
							font-size: 12px;
							font-weight: 600;
							text-transform: uppercase;
						}
						.status-completed {
							background-color: #dcfce7;
							color: #166534;
						}
						.status-pending {
							background-color: #fef3c7;
							color: #92400e;
						}
						.status-failed {
							background-color: #fee2e2;
							color: #991b1b;
						}
					</style>
				</head>
				<body>
					<div class="header">
						<h1>AI Labs Africa</h1>
						<h2>INVOICE</h2>
					</div>
					
					<div class="invoice-details">
						<div>
							<p><strong>Invoice Number:</strong> ${invoiceData.invoiceNumber}</p>
							<p><strong>Date:</strong> ${invoiceData.date}</p>
							<p><strong>Due Date:</strong> ${invoiceData.dueDate}</p>
						</div>
						<div>
							<p><strong>Status:</strong> 
								<span class="status-badge status-${invoiceData.status}">
									${invoiceData.status.toUpperCase()}
								</span>
							</p>
							<p><strong>Transaction ID:</strong> ${transactionId}</p>
						</div>
					</div>
					
					<div class="customer-details">
						<h3>Bill To:</h3>
						<p><strong>${invoiceData.customer.name}</strong></p>
						${invoiceData.customer.company ? `<p>${invoiceData.customer.company}</p>` : ''}
						<p>${invoiceData.customer.email}</p>
						${invoiceData.customer.phone ? `<p>${invoiceData.customer.phone}</p>` : ''}
					</div>
					
					<table>
						<thead>
							<tr>
								<th>Description</th>
								<th>Quantity</th>
								<th>Unit Price</th>
								<th>Amount</th>
							</tr>
						</thead>
						<tbody>
							${invoiceData.items.map(item => `
								<tr>
									<td>${item.description}</td>
									<td>${item.quantity}</td>
									<td>$${item.unitPrice.toFixed(2)}</td>
									<td>$${item.amount.toFixed(2)}</td>
								</tr>
							`).join('')}
						</tbody>
					</table>
					
					<div class="total">
						<p>Subtotal: $${invoiceData.subtotal.toFixed(2)}</p>
						<p>Tax: $${invoiceData.tax.toFixed(2)}</p>
						<p style="font-size: 18px; color: #2563eb;">Total: $${invoiceData.total.toFixed(2)}</p>
					</div>
					
					<div class="footer">
						<p>Thank you for your business!</p>
						<p><strong>AI Labs Africa</strong></p>
						<p>Transforming businesses with AI innovation</p>
					</div>
				</body>
			</html>
		`;

		// For now, we'll return the HTML content
		// In production, you would convert this to PDF using a service like:
		// - Puppeteer
		// - jsPDF
		// - Cloud PDF generation service (e.g., DocRaptor, PDFShift)

		// Store the invoice data in the database
		const { error: dbError } = await supabase
			.from('invoices')
			.insert([{
				invoice_number: invoiceData.invoiceNumber,
				transaction_id: transactionId,
				customer_name: invoiceData.customer.name,
				customer_email: invoiceData.customer.email,
				amount: invoiceData.total,
				status: invoiceData.status,
				invoice_data: invoiceData,
				created_at: new Date().toISOString()
			}])

		if (dbError) {
			console.error('Database error:', dbError)
			// Don't fail the request, just log the error
		}

		// Return the HTML content for now
		// In production, you would return a PDF URL
		return new Response(
			JSON.stringify({
				success: true,
				html: pdfHtml,
				invoiceNumber: invoiceData.invoiceNumber,
				message: 'Invoice generated successfully'
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)

	} catch (error) {
		console.error('Invoice generation error:', error)
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
