/**
 * Role-based access control system
 * Defines user roles and their permissions
 */

export enum UserRole {
	ADMIN = 'admin',
	USER = 'user',
	DEMO = 'demo',
	GUEST = 'guest'
}

export interface Permission {
	resource: string;
	actions: string[];
}

export interface Role {
	name: UserRole;
	displayName: string;
	description: string;
	permissions: Permission[];
}

export const ROLES: Record<UserRole, Role> = {
	[UserRole.ADMIN]: {
		name: UserRole.ADMIN,
		displayName: 'Administrator',
		description: 'Full system access with user management capabilities',
		permissions: [
			{ resource: 'users', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'assistants', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'demos', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'payments', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'analytics', actions: ['read'] },
			{ resource: 'system', actions: ['read', 'update'] }
		]
	},
	[UserRole.USER]: {
		name: UserRole.USER,
		displayName: 'User',
		description: 'Standard user with full access to personal features',
		permissions: [
			{ resource: 'assistants', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'demos', actions: ['read', 'create', 'update', 'delete'] },
			{ resource: 'payments', actions: ['read', 'create'] },
			{ resource: 'analytics', actions: ['read'] }
		]
	},
	[UserRole.DEMO]: {
		name: UserRole.DEMO,
		displayName: 'Demo User',
		description: 'Limited access for demo purposes',
		permissions: [
			{ resource: 'demos', actions: ['read'] },
			{ resource: 'assistants', actions: ['read'] }
		]
	},
	[UserRole.GUEST]: {
		name: UserRole.GUEST,
		displayName: 'Guest',
		description: 'Public access with minimal permissions',
		permissions: [
			{ resource: 'demos', actions: ['read'] }
		]
	}
};

/**
 * Check if a user has permission to perform an action on a resource
 */
export function hasPermission(
	userRole: UserRole | null,
	resource: string,
	action: string
): boolean {
	if (!userRole || !ROLES[userRole]) {
		return false;
	}

	const role = ROLES[userRole];
	const permission = role.permissions.find(p => p.resource === resource);

	return permission ? permission.actions.includes(action) : false;
}

/**
 * Get all permissions for a user role
 */
export function getRolePermissions(userRole: UserRole | null): Permission[] {
	if (!userRole || !ROLES[userRole]) {
		return [];
	}

	return ROLES[userRole].permissions;
}

/**
 * Get role display name
 */
export function getRoleDisplayName(userRole: UserRole | null): string {
	if (!userRole || !ROLES[userRole]) {
		return 'Unknown';
	}

	return ROLES[userRole].displayName;
}

/**
 * Get role description
 */
export function getRoleDescription(userRole: UserRole | null): string {
	if (!userRole || !ROLES[userRole]) {
		return '';
	}

	return ROLES[userRole].description;
}

/**
 * Check if user can access a specific route
 */
export function canAccessRoute(userRole: UserRole | null, route: string): boolean {
	const routePermissions: Record<string, { resource: string; action: string }> = {
		'/dashboard': { resource: 'analytics', action: 'read' },
		'/create-assistant': { resource: 'assistants', action: 'create' },
		'/voice-agents': { resource: 'assistants', action: 'read' },
		'/custom-demos': { resource: 'demos', action: 'read' },
		'/admin': { resource: 'system', action: 'read' }
	};

	const permission = routePermissions[route];
	if (!permission) {
		return true; // Allow access if no specific permission is required
	}

	return hasPermission(userRole, permission.resource, permission.action);
}
