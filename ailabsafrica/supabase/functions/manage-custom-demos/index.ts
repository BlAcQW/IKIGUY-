import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ManageCustomDemoRequest {
	action: 'delete' | 'get' | 'list';
	demo_id?: string;
	user_id?: string;
	guest_email?: string;
	guest_password?: string;
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
		const { action, demo_id, user_id, guest_email, guest_password }: ManageCustomDemoRequest = await req.json()

		if (!action) {
			return new Response(
				JSON.stringify({ error: 'Missing required field: action is required' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		// Handle authentication - support both authenticated users and guest users
		let authenticatedUserId: string | null = null;
		let guestUserEmail: string | null = null;

		// Try to get authenticated user first
		const authHeader = req.headers.get('authorization');
		if (authHeader) {
			try {
				const { data: { user }, error } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));
				if (user && !error) {
					authenticatedUserId = user.id;
				}
			} catch (error) {
				console.log('Auth header present but invalid, trying guest mode');
			}
		}

		// If no authenticated user, try guest mode
		if (!authenticatedUserId && guest_email && guest_password) {
			guestUserEmail = guest_email;
		}

		// For delete action, require demo_id
		if (action === 'delete' && !demo_id) {
			return new Response(
				JSON.stringify({ error: 'demo_id is required for delete action' }),
				{
					status: 400,
					headers: { ...corsHeaders, 'Content-Type': 'application/json' }
				}
			)
		}

		switch (action) {
			case 'delete':
				// Get the demo to verify ownership and get VAPI assistant ID
				let demoQuery = supabase
					.from('custom_demos')
					.select('*')
					.eq('id', demo_id);

				// Apply ownership filter based on authentication type
				if (authenticatedUserId) {
					demoQuery = demoQuery.eq('user_id', authenticatedUserId);
				} else if (guestUserEmail) {
					demoQuery = demoQuery.eq('guest_email', guestUserEmail);
				} else {
					return new Response(
						JSON.stringify({ error: 'Authentication required' }),
						{
							status: 401,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				const { data: demo, error: demoError } = await demoQuery.single();

				if (demoError || !demo) {
					return new Response(
						JSON.stringify({ error: 'Demo not found or access denied' }),
						{
							status: 404,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				// Delete from VAPI if assistant_id exists
				if (demo.assistant_id) {
					try {
						const vapiPrivateKey = Deno.env.get('VAPI_PRIVATE_KEY');
						if (vapiPrivateKey) {
							console.log(`[manage-custom-demos] Deleting VAPI assistant: ${demo.assistant_id}`);

							const vapiResponse = await fetch(`https://api.vapi.ai/assistant/${demo.assistant_id}`, {
								method: 'DELETE',
								headers: {
									'Authorization': `Bearer ${vapiPrivateKey}`,
									'Content-Type': 'application/json'
								}
							});

							if (vapiResponse.ok) {
								console.log(`[manage-custom-demos] Successfully deleted VAPI assistant: ${demo.assistant_id}`);
							} else {
								const errorText = await vapiResponse.text();
								console.error(`[manage-custom-demos] Failed to delete VAPI assistant: ${demo.assistant_id}`, errorText);
								// Don't fail the request if VAPI deletion fails
							}
						} else {
							console.warn('[manage-custom-demos] VAPI_PRIVATE_KEY not found, skipping VAPI deletion');
						}
					} catch (vapiError) {
						console.error('[manage-custom-demos] VAPI deletion error:', vapiError);
						// Don't fail the request if VAPI deletion fails
					}
				}

				// Delete from database
				let deleteQuery = supabase
					.from('custom_demos')
					.delete()
					.eq('id', demo_id);

				// Apply ownership filter for deletion
				if (authenticatedUserId) {
					deleteQuery = deleteQuery.eq('user_id', authenticatedUserId);
				} else if (guestUserEmail) {
					deleteQuery = deleteQuery.eq('guest_email', guestUserEmail);
				}

				const { error: deleteError } = await deleteQuery;

				if (deleteError) {
					console.error('[manage-custom-demos] Database deletion error:', deleteError);
					return new Response(
						JSON.stringify({ error: 'Failed to delete demo from database' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				return new Response(
					JSON.stringify({
						success: true,
						message: 'Demo deleted successfully',
						deleted_demo: demo
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				);

			case 'get':
				if (!demo_id) {
					return new Response(
						JSON.stringify({ error: 'demo_id is required for get action' }),
						{
							status: 400,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				let getQuery = supabase
					.from('custom_demos')
					.select('*')
					.eq('id', demo_id);

				if (authenticatedUserId) {
					getQuery = getQuery.eq('user_id', authenticatedUserId);
				} else if (guestUserEmail) {
					getQuery = getQuery.eq('guest_email', guestUserEmail);
				} else {
					return new Response(
						JSON.stringify({ error: 'Authentication required' }),
						{
							status: 401,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				const { data: demoData, error: getError } = await getQuery.single();

				if (getError || !demoData) {
					return new Response(
						JSON.stringify({ error: 'Demo not found or access denied' }),
						{
							status: 404,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				return new Response(
					JSON.stringify({
						success: true,
						demo: demoData
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				);

			case 'list':
				let listQuery = supabase
					.from('custom_demos')
					.select('*')
					.order('created_at', { ascending: false });

				if (authenticatedUserId) {
					listQuery = listQuery.eq('user_id', authenticatedUserId);
				} else if (guestUserEmail) {
					listQuery = listQuery.eq('guest_email', guestUserEmail);
				} else {
					return new Response(
						JSON.stringify({ error: 'Authentication required' }),
						{
							status: 401,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				const { data: demos, error: listError } = await listQuery;

				if (listError) {
					console.error('[manage-custom-demos] List error:', listError);
					return new Response(
						JSON.stringify({ error: 'Failed to list demos' }),
						{
							status: 500,
							headers: { ...corsHeaders, 'Content-Type': 'application/json' }
						}
					)
				}

				return new Response(
					JSON.stringify({
						success: true,
						demos: demos || []
					}),
					{
						status: 200,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				);

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action. Use "delete", "get", or "list"' }),
					{
						status: 400,
						headers: { ...corsHeaders, 'Content-Type': 'application/json' }
					}
				)
		}

	} catch (error) {
		console.error('[manage-custom-demos] Error:', error);
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

