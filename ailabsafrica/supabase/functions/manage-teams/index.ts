import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		// Create Supabase client
		const supabaseClient = createClient(
			Deno.env.get('SUPABASE_URL') ?? '',
			Deno.env.get('SUPABASE_ANON_KEY') ?? '',
			{
				global: {
					headers: { Authorization: req.headers.get('Authorization')! },
				},
			}
		)

		// Get the current user
		const { data: { user }, error: userError } = await supabaseClient.auth.getUser()
		if (userError || !user) {
			return new Response(
				JSON.stringify({ error: 'Unauthorized' }),
				{ status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
			)
		}

		const { action, ...params } = await req.json()

		switch (action) {
			case 'create_team':
				return await handleCreateTeam(supabaseClient, user.id, params)

			case 'get_user_teams':
				return await handleGetUserTeams(supabaseClient, user.id)

			case 'get_team_details':
				return await handleGetTeamDetails(supabaseClient, user.id, params.team_id)

			case 'update_team':
				return await handleUpdateTeam(supabaseClient, user.id, params)

			case 'delete_team':
				return await handleDeleteTeam(supabaseClient, user.id, params.team_id)

			case 'get_team_members':
				return await handleGetTeamMembers(supabaseClient, user.id, params.team_id)

			case 'invite_member':
				return await handleInviteMember(supabaseClient, user.id, params)

			case 'accept_invitation':
				return await handleAcceptInvitation(supabaseClient, user.id, params.token)

			case 'decline_invitation':
				return await handleDeclineInvitation(supabaseClient, user.id, params.token)

			case 'update_member_role':
				return await handleUpdateMemberRole(supabaseClient, user.id, params)

			case 'remove_member':
				return await handleRemoveMember(supabaseClient, user.id, params)

			case 'get_team_invitations':
				return await handleGetTeamInvitations(supabaseClient, user.id, params.team_id)

			case 'cancel_invitation':
				return await handleCancelInvitation(supabaseClient, user.id, params.invitation_id)

			case 'get_team_resources':
				return await handleGetTeamResources(supabaseClient, user.id, params.team_id)

			case 'share_resource':
				return await handleShareResource(supabaseClient, user.id, params)

			case 'unshare_resource':
				return await handleUnshareResource(supabaseClient, user.id, params)

			case 'get_team_activity':
				return await handleGetTeamActivity(supabaseClient, user.id, params.team_id)

			case 'get_team_settings':
				return await handleGetTeamSettings(supabaseClient, user.id, params.team_id)

			case 'update_team_settings':
				return await handleUpdateTeamSettings(supabaseClient, user.id, params)

			default:
				return new Response(
					JSON.stringify({ error: 'Invalid action' }),
					{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
				)
		}
	} catch (error) {
		console.error('Error:', error)
		return new Response(
			JSON.stringify({ error: 'Internal server error' }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}
})

// Create a new team
async function handleCreateTeam(supabase: any, userId: string, params: any) {
	const { name, description, slug } = params

	if (!name || !slug) {
		return new Response(
			JSON.stringify({ error: 'Name and slug are required' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Check if slug is unique
	const { data: existingTeam } = await supabase
		.from('teams')
		.select('id')
		.eq('slug', slug)
		.single()

	if (existingTeam) {
		return new Response(
			JSON.stringify({ error: 'Team slug already exists' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Create team
	const { data: team, error: teamError } = await supabase
		.from('teams')
		.insert({
			name,
			description,
			slug,
			owner_id: userId
		})
		.select()
		.single()

	if (teamError) {
		return new Response(
			JSON.stringify({ error: teamError.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Add owner as team member with owner role
	const { data: ownerRole } = await supabase
		.from('team_roles')
		.select('id')
		.eq('name', 'owner')
		.single()

	if (ownerRole) {
		await supabase
			.from('team_members')
			.insert({
				team_id: team.id,
				user_id: userId,
				role_id: ownerRole.id,
				status: 'active',
				accepted_at: new Date().toISOString()
			})
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team.id,
		action_name: 'team_created',
		details: { team_name: name }
	})

	return new Response(
		JSON.stringify({ data: team }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get user's teams
async function handleGetUserTeams(supabase: any, userId: string) {
	const { data, error } = await supabase.rpc('get_user_teams', { user_uuid: userId })

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team details
async function handleGetTeamDetails(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('teams')
		.select(`
      *,
      team_members!inner(id, user_id, status),
      team_roles!inner(name, display_name)
    `)
		.eq('id', teamId)
		.single()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Update team
async function handleUpdateTeam(supabase: any, userId: string, params: any) {
	const { team_id, name, description } = params

	// Check if user is team owner
	const { data: team } = await supabase
		.from('teams')
		.select('owner_id')
		.eq('id', team_id)
		.single()

	if (!team || team.owner_id !== userId) {
		return new Response(
			JSON.stringify({ error: 'Only team owners can update team details' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('teams')
		.update({ name, description })
		.eq('id', team_id)
		.select()
		.single()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team_id,
		action_name: 'team_updated',
		details: { name, description }
	})

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Delete team
async function handleDeleteTeam(supabase: any, userId: string, teamId: string) {
	// Check if user is team owner
	const { data: team } = await supabase
		.from('teams')
		.select('owner_id, name')
		.eq('id', teamId)
		.single()

	if (!team || team.owner_id !== userId) {
		return new Response(
			JSON.stringify({ error: 'Only team owners can delete teams' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { error } = await supabase
		.from('teams')
		.delete()
		.eq('id', teamId)

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ message: 'Team deleted successfully' }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team members
async function handleGetTeamMembers(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase.rpc('get_team_members', { team_uuid: teamId })

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Invite member to team
async function handleInviteMember(supabase: any, userId: string, params: any) {
	const { team_id, email, role_name } = params

	// Check if user can invite members
	const hasPermission = await supabase.rpc('check_team_permission', {
		team_uuid: team_id,
		permission_name: 'invite_members',
		user_uuid: userId
	})

	if (!hasPermission.data) {
		return new Response(
			JSON.stringify({ error: 'You do not have permission to invite members' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Get role
	const { data: role } = await supabase
		.from('team_roles')
		.select('id')
		.eq('name', role_name)
		.single()

	if (!role) {
		return new Response(
			JSON.stringify({ error: 'Invalid role' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Generate invitation token
	const token = crypto.randomUUID()
	const expiresAt = new Date()
	expiresAt.setDate(expiresAt.getDate() + 7) // 7 days expiry

	const { data, error } = await supabase
		.from('team_invitations')
		.insert({
			team_id,
			email,
			role_id: role.id,
			invited_by: userId,
			token,
			expires_at: expiresAt.toISOString()
		})
		.select()
		.single()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team_id,
		action_name: 'member_invited',
		details: { email, role_name }
	})

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Accept invitation
async function handleAcceptInvitation(supabase: any, userId: string, token: string) {
	// Get invitation
	const { data: invitation, error: invitationError } = await supabase
		.from('team_invitations')
		.select('*')
		.eq('token', token)
		.eq('status', 'pending')
		.single()

	if (invitationError || !invitation) {
		return new Response(
			JSON.stringify({ error: 'Invalid or expired invitation' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	if (new Date() > new Date(invitation.expires_at)) {
		return new Response(
			JSON.stringify({ error: 'Invitation has expired' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Check if user is already a member
	const { data: existingMember } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', invitation.team_id)
		.eq('user_id', userId)
		.single()

	if (existingMember) {
		return new Response(
			JSON.stringify({ error: 'You are already a member of this team' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Add user as team member
	const { data: member, error: memberError } = await supabase
		.from('team_members')
		.insert({
			team_id: invitation.team_id,
			user_id: userId,
			role_id: invitation.role_id,
			status: 'active',
			invited_by: invitation.invited_by,
			accepted_at: new Date().toISOString()
		})
		.select()
		.single()

	if (memberError) {
		return new Response(
			JSON.stringify({ error: memberError.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Update invitation status
	await supabase
		.from('team_invitations')
		.update({ status: 'accepted' })
		.eq('id', invitation.id)

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: invitation.team_id,
		action_name: 'invitation_accepted',
		details: { user_id: userId }
	})

	return new Response(
		JSON.stringify({ data: member }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Decline invitation
async function handleDeclineInvitation(supabase: any, userId: string, token: string) {
	const { data: invitation, error: invitationError } = await supabase
		.from('team_invitations')
		.select('*')
		.eq('token', token)
		.eq('status', 'pending')
		.single()

	if (invitationError || !invitation) {
		return new Response(
			JSON.stringify({ error: 'Invalid invitation' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Update invitation status
	await supabase
		.from('team_invitations')
		.update({ status: 'declined' })
		.eq('id', invitation.id)

	return new Response(
		JSON.stringify({ message: 'Invitation declined' }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Update member role
async function handleUpdateMemberRole(supabase: any, userId: string, params: any) {
	const { team_id, member_user_id, new_role_name } = params

	// Check if user can change roles
	const hasPermission = await supabase.rpc('check_team_permission', {
		team_uuid: team_id,
		permission_name: 'change_roles',
		user_uuid: userId
	})

	if (!hasPermission.data) {
		return new Response(
			JSON.stringify({ error: 'You do not have permission to change roles' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Get new role
	const { data: role } = await supabase
		.from('team_roles')
		.select('id')
		.eq('name', new_role_name)
		.single()

	if (!role) {
		return new Response(
			JSON.stringify({ error: 'Invalid role' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Update member role
	const { data, error } = await supabase
		.from('team_members')
		.update({ role_id: role.id })
		.eq('team_id', team_id)
		.eq('user_id', member_user_id)
		.select()
		.single()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team_id,
		action_name: 'role_changed',
		details: { member_user_id, new_role_name }
	})

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Remove member from team
async function handleRemoveMember(supabase: any, userId: string, params: any) {
	const { team_id, member_user_id } = params

	// Check if user can remove members
	const hasPermission = await supabase.rpc('check_team_permission', {
		team_uuid: team_id,
		permission_name: 'remove_members',
		user_uuid: userId
	})

	if (!hasPermission.data) {
		return new Response(
			JSON.stringify({ error: 'You do not have permission to remove members' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Remove member
	const { error } = await supabase
		.from('team_members')
		.delete()
		.eq('team_id', team_id)
		.eq('user_id', member_user_id)

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team_id,
		action_name: 'member_removed',
		details: { member_user_id }
	})

	return new Response(
		JSON.stringify({ message: 'Member removed successfully' }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team invitations
async function handleGetTeamInvitations(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('team_invitations')
		.select(`
      *,
      team_roles(name, display_name)
    `)
		.eq('team_id', teamId)
		.order('created_at', { ascending: false })

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Cancel invitation
async function handleCancelInvitation(supabase: any, userId: string, invitationId: string) {
	// Get invitation
	const { data: invitation } = await supabase
		.from('team_invitations')
		.select('team_id, status')
		.eq('id', invitationId)
		.single()

	if (!invitation || invitation.status !== 'pending') {
		return new Response(
			JSON.stringify({ error: 'Invalid invitation' }),
			{ status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Check if user can manage invitations
	const hasPermission = await supabase.rpc('check_team_permission', {
		team_uuid: invitation.team_id,
		permission_name: 'manage_members',
		user_uuid: userId
	})

	if (!hasPermission.data) {
		return new Response(
			JSON.stringify({ error: 'You do not have permission to cancel invitations' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Cancel invitation
	await supabase
		.from('team_invitations')
		.update({ status: 'cancelled' })
		.eq('id', invitationId)

	return new Response(
		JSON.stringify({ message: 'Invitation cancelled' }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team resources
async function handleGetTeamResources(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('team_resources')
		.select('*')
		.eq('team_id', teamId)
		.order('created_at', { ascending: false })

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Share resource with team
async function handleShareResource(supabase: any, userId: string, params: any) {
	const { team_id, resource_type, resource_id, resource_name, permissions, is_public } = params

	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', team_id)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('team_resources')
		.insert({
			team_id,
			resource_type,
			resource_id,
			resource_name,
			shared_by: userId,
			permissions: permissions || { read: true, write: false, delete: false },
			is_public: is_public || false
		})
		.select()
		.single()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Log activity
	await supabase.rpc('log_team_activity', {
		team_uuid: team_id,
		action_name: 'resource_shared',
		resource_type,
		resource_uuid: resource_id,
		details: { resource_name }
	})

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Unshare resource
async function handleUnshareResource(supabase: any, userId: string, params: any) {
	const { team_id, resource_id } = params

	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', team_id)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { error } = await supabase
		.from('team_resources')
		.delete()
		.eq('team_id', team_id)
		.eq('resource_id', resource_id)

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ message: 'Resource unshared successfully' }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team activity
async function handleGetTeamActivity(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('team_activity_log')
		.select('*')
		.eq('team_id', teamId)
		.order('created_at', { ascending: false })
		.limit(50)

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Get team settings
async function handleGetTeamSettings(supabase: any, userId: string, teamId: string) {
	// Check if user has access to team
	const { data: member } = await supabase
		.from('team_members')
		.select('id')
		.eq('team_id', teamId)
		.eq('user_id', userId)
		.eq('status', 'active')
		.single()

	if (!member) {
		return new Response(
			JSON.stringify({ error: 'Access denied' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	const { data, error } = await supabase
		.from('team_settings')
		.select('*')
		.eq('team_id', teamId)

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}

// Update team settings
async function handleUpdateTeamSettings(supabase: any, userId: string, params: any) {
	const { team_id, settings } = params

	// Check if user can manage settings
	const hasPermission = await supabase.rpc('check_team_permission', {
		team_uuid: team_id,
		permission_name: 'manage_settings',
		user_uuid: userId
	})

	if (!hasPermission.data) {
		return new Response(
			JSON.stringify({ error: 'You do not have permission to update settings' }),
			{ status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	// Update settings
	const settingsArray = Object.entries(settings).map(([key, value]) => ({
		team_id,
		setting_key: key,
		setting_value: value
	}))

	const { data, error } = await supabase
		.from('team_settings')
		.upsert(settingsArray, { onConflict: 'team_id,setting_key' })
		.select()

	if (error) {
		return new Response(
			JSON.stringify({ error: error.message }),
			{ status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
		)
	}

	return new Response(
		JSON.stringify({ data }),
		{ headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
	)
}
