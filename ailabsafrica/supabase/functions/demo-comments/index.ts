import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CreateCommentRequest {
	demo_id: string;
	user_name: string;
	user_email?: string;
	rating?: number;
	comment_text: string;
	user_agent?: string;
	ip_address?: string;
}

interface AddReplyRequest {
	comment_id: string;
	reply_text: string;
	is_public?: boolean;
}

interface GetCommentsRequest {
	demo_id: string;
	limit?: number;
	offset?: number;
}

interface GetCommentStatsRequest {
	demo_id: string;
}

interface ApproveCommentRequest {
	comment_id: string;
	is_approved: boolean;
}

interface FlagCommentRequest {
	comment_id: string;
	is_flagged: boolean;
	flagged_reason?: string;
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

		// Get the action from the URL
		const url = new URL(req.url)
		const action = url.searchParams.get('action')

		// Get the request body
		const requestBody = await req.json()

		switch (action) {
			case 'create_comment':
				return await handleCreateComment(supabase, requestBody as CreateCommentRequest)

			case 'add_reply':
				return await handleAddReply(supabase, requestBody as AddReplyRequest)

			case 'get_comments':
				return await handleGetComments(supabase, requestBody as GetCommentsRequest)

			case 'get_comment_stats':
				return await handleGetCommentStats(supabase, requestBody as GetCommentStatsRequest)

			case 'approve_comment':
				return await handleApproveComment(supabase, requestBody as ApproveCommentRequest)

			case 'flag_comment':
				return await handleFlagComment(supabase, requestBody as FlagCommentRequest)

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
		}
	} catch (error) {
		console.error('Error in demo-comments function:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
})

async function handleCreateComment(supabase: any, request: CreateCommentRequest) {
	const { demo_id, user_name, user_email, rating, comment_text, user_agent, ip_address } = request

	if (!demo_id || !user_name || !comment_text) {
		return new Response(
			JSON.stringify({ error: 'demo_id, user_name, and comment_text are required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	if (rating && (rating < 1 || rating > 5)) {
		return new Response(
			JSON.stringify({ error: 'rating must be between 1 and 5' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Insert the comment
		const { data, error } = await supabase
			.from('demo_comments')
			.insert({
				demo_id,
				user_name,
				user_email,
				rating,
				comment_text,
				user_agent,
				ip_address: ip_address ? ip_address : null,
				is_approved: false // Comments require approval by default
			})
			.select()
			.single()

		if (error) {
			console.error('Error creating comment:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				comment: data,
				message: 'Comment submitted successfully and awaiting approval'
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleCreateComment:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to create comment' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleAddReply(supabase: any, request: AddReplyRequest) {
	const { comment_id, reply_text, is_public = true } = request

	if (!comment_id || !reply_text) {
		return new Response(
			JSON.stringify({ error: 'comment_id and reply_text are required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Get the current user
		const authHeader = req.headers.get('authorization')
		if (!authHeader) {
			return new Response(
				JSON.stringify({ error: 'Authentication required' }),
				{
					status: 401,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		const { data: { user }, error: authError } = await supabase.auth.getUser(
			authHeader.replace('Bearer ', '')
		)

		if (authError || !user) {
			return new Response(
				JSON.stringify({ error: 'Invalid authentication' }),
				{
					status: 401,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Insert the reply
		const { data, error } = await supabase
			.from('demo_comment_replies')
			.insert({
				comment_id,
				user_id: user.id,
				reply_text,
				is_public
			})
			.select()
			.single()

		if (error) {
			console.error('Error adding reply:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				reply: data,
				message: 'Reply added successfully'
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleAddReply:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to add reply' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleGetComments(supabase: any, request: GetCommentsRequest) {
	const { demo_id, limit = 50, offset = 0 } = request

	if (!demo_id) {
		return new Response(
			JSON.stringify({ error: 'demo_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Call the database function to get comments with replies
		const { data, error } = await supabase.rpc('get_demo_comments_with_replies', {
			p_demo_id: demo_id,
			p_limit: limit,
			p_offset: offset
		})

		if (error) {
			console.error('Error getting comments:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				comments: data || []
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleGetComments:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to get comments' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleGetCommentStats(supabase: any, request: GetCommentStatsRequest) {
	const { demo_id } = request

	if (!demo_id) {
		return new Response(
			JSON.stringify({ error: 'demo_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Call the database function to get comment statistics
		const { data, error } = await supabase.rpc('get_demo_comment_stats', {
			p_demo_id: demo_id
		})

		if (error) {
			console.error('Error getting comment stats:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				stats: data?.[0] || {
					total_comments: 0,
					approved_comments: 0,
					average_rating: 0,
					rating_distribution: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
				}
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleGetCommentStats:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to get comment stats' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleApproveComment(supabase: any, request: ApproveCommentRequest) {
	const { comment_id, is_approved } = request

	if (!comment_id) {
		return new Response(
			JSON.stringify({ error: 'comment_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Update the comment approval status
		const { data, error } = await supabase
			.from('demo_comments')
			.update({ is_approved })
			.eq('id', comment_id)
			.select()
			.single()

		if (error) {
			console.error('Error approving comment:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				comment: data,
				message: `Comment ${is_approved ? 'approved' : 'unapproved'} successfully`
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleApproveComment:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to approve comment' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}

async function handleFlagComment(supabase: any, request: FlagCommentRequest) {
	const { comment_id, is_flagged, flagged_reason } = request

	if (!comment_id) {
		return new Response(
			JSON.stringify({ error: 'comment_id is required' }),
			{
				status: 400,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}

	try {
		// Update the comment flag status
		const { data, error } = await supabase
			.from('demo_comments')
			.update({
				is_flagged,
				flagged_reason: is_flagged ? flagged_reason : null
			})
			.eq('id', comment_id)
			.select()
			.single()

		if (error) {
			console.error('Error flagging comment:', error)
			return new Response(
				JSON.stringify({ error: error.message }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		return new Response(
			JSON.stringify({
				success: true,
				comment: data,
				message: `Comment ${is_flagged ? 'flagged' : 'unflagged'} successfully`
			}),
			{
				status: 200,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	} catch (error) {
		console.error('Error in handleFlagComment:', error)
		return new Response(
			JSON.stringify({ error: 'Failed to flag comment' }),
			{
				status: 500,
				headers: { ...corsHeaders, 'Content-Type': 'application/json' }
			}
		)
	}
}
