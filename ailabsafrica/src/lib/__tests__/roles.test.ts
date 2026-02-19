import {
	UserRole,
	ROLES,
	hasPermission,
	getRolePermissions,
	getRoleDisplayName,
	getRoleDescription,
	canAccessRoute
} from '../roles';

describe('Role-Based Access Control', () => {
	describe('UserRole enum', () => {
		it('should have the correct role values', () => {
			expect(UserRole.ADMIN).toBe('admin');
			expect(UserRole.USER).toBe('user');
			expect(UserRole.DEMO).toBe('demo');
			expect(UserRole.GUEST).toBe('guest');
		});
	});

	describe('ROLES configuration', () => {
		it('should have all required roles defined', () => {
			expect(ROLES[UserRole.ADMIN]).toBeDefined();
			expect(ROLES[UserRole.USER]).toBeDefined();
			expect(ROLES[UserRole.DEMO]).toBeDefined();
			expect(ROLES[UserRole.GUEST]).toBeDefined();
		});

		it('should have correct role properties', () => {
			const adminRole = ROLES[UserRole.ADMIN];
			expect(adminRole.name).toBe(UserRole.ADMIN);
			expect(adminRole.displayName).toBe('Administrator');
			expect(adminRole.description).toBe('Full system access with user management capabilities');
			expect(adminRole.permissions).toBeInstanceOf(Array);
		});

		it('should have permissions for each role', () => {
			Object.values(ROLES).forEach(role => {
				expect(role.permissions).toBeInstanceOf(Array);
				expect(role.permissions.length).toBeGreaterThan(0);

				role.permissions.forEach(permission => {
					expect(permission.resource).toBeDefined();
					expect(permission.actions).toBeInstanceOf(Array);
					expect(permission.actions.length).toBeGreaterThan(0);
				});
			});
		});
	});

	describe('hasPermission function', () => {
		it('should return false for null role', () => {
			expect(hasPermission(null, 'users', 'read')).toBe(false);
		});

		it('should return false for invalid role', () => {
			expect(hasPermission('invalid-role' as UserRole, 'users', 'read')).toBe(false);
		});

		it('should return true for admin with full permissions', () => {
			expect(hasPermission(UserRole.ADMIN, 'users', 'read')).toBe(true);
			expect(hasPermission(UserRole.ADMIN, 'users', 'create')).toBe(true);
			expect(hasPermission(UserRole.ADMIN, 'users', 'update')).toBe(true);
			expect(hasPermission(UserRole.ADMIN, 'users', 'delete')).toBe(true);
		});

		it('should return false for user without permission', () => {
			expect(hasPermission(UserRole.USER, 'users', 'delete')).toBe(false);
		});

		it('should return true for user with valid permission', () => {
			expect(hasPermission(UserRole.USER, 'assistants', 'read')).toBe(true);
			expect(hasPermission(UserRole.USER, 'assistants', 'create')).toBe(true);
		});

		it('should return false for demo user with limited permissions', () => {
			expect(hasPermission(UserRole.DEMO, 'assistants', 'create')).toBe(false);
			expect(hasPermission(UserRole.DEMO, 'payments', 'read')).toBe(false);
		});

		it('should return true for demo user with allowed permissions', () => {
			expect(hasPermission(UserRole.DEMO, 'demos', 'read')).toBe(true);
			expect(hasPermission(UserRole.DEMO, 'assistants', 'read')).toBe(true);
		});

		it('should return false for guest with minimal permissions', () => {
			expect(hasPermission(UserRole.GUEST, 'assistants', 'read')).toBe(false);
			expect(hasPermission(UserRole.GUEST, 'payments', 'read')).toBe(false);
		});

		it('should return true for guest with allowed permissions', () => {
			expect(hasPermission(UserRole.GUEST, 'demos', 'read')).toBe(true);
		});
	});

	describe('getRolePermissions function', () => {
		it('should return empty array for null role', () => {
			expect(getRolePermissions(null)).toEqual([]);
		});

		it('should return empty array for invalid role', () => {
			expect(getRolePermissions('invalid-role' as UserRole)).toEqual([]);
		});

		it('should return permissions for valid role', () => {
			const adminPermissions = getRolePermissions(UserRole.ADMIN);
			expect(adminPermissions).toBeInstanceOf(Array);
			expect(adminPermissions.length).toBeGreaterThan(0);

			const userPermissions = getRolePermissions(UserRole.USER);
			expect(userPermissions).toBeInstanceOf(Array);
			expect(userPermissions.length).toBeGreaterThan(0);
		});

		it('should return correct permissions for each role', () => {
			const adminPermissions = getRolePermissions(UserRole.ADMIN);
			const userPermissions = getRolePermissions(UserRole.USER);
			const demoPermissions = getRolePermissions(UserRole.DEMO);
			const guestPermissions = getRolePermissions(UserRole.GUEST);

			// Admin should have more permissions than other roles
			expect(adminPermissions.length).toBeGreaterThan(userPermissions.length);
			expect(adminPermissions.length).toBeGreaterThan(demoPermissions.length);
			expect(adminPermissions.length).toBeGreaterThan(guestPermissions.length);

			// Guest should have the least permissions
			expect(guestPermissions.length).toBeLessThan(demoPermissions.length);
			expect(guestPermissions.length).toBeLessThan(userPermissions.length);
		});
	});

	describe('getRoleDisplayName function', () => {
		it('should return "Unknown" for null role', () => {
			expect(getRoleDisplayName(null)).toBe('Unknown');
		});

		it('should return "Unknown" for invalid role', () => {
			expect(getRoleDisplayName('invalid-role' as UserRole)).toBe('Unknown');
		});

		it('should return correct display names for valid roles', () => {
			expect(getRoleDisplayName(UserRole.ADMIN)).toBe('Administrator');
			expect(getRoleDisplayName(UserRole.USER)).toBe('User');
			expect(getRoleDisplayName(UserRole.DEMO)).toBe('Demo User');
			expect(getRoleDisplayName(UserRole.GUEST)).toBe('Guest');
		});
	});

	describe('getRoleDescription function', () => {
		it('should return empty string for null role', () => {
			expect(getRoleDescription(null)).toBe('');
		});

		it('should return empty string for invalid role', () => {
			expect(getRoleDescription('invalid-role' as UserRole)).toBe('');
		});

		it('should return correct descriptions for valid roles', () => {
			expect(getRoleDescription(UserRole.ADMIN)).toBe('Full system access with user management capabilities');
			expect(getRoleDescription(UserRole.USER)).toBe('Standard user with full access to personal features');
			expect(getRoleDescription(UserRole.DEMO)).toBe('Limited access for demo purposes');
			expect(getRoleDescription(UserRole.GUEST)).toBe('Public access with minimal permissions');
		});
	});

	describe('canAccessRoute function', () => {
		it('should return true for routes without specific permissions', () => {
			expect(canAccessRoute(UserRole.USER, '/home')).toBe(true);
			expect(canAccessRoute(UserRole.GUEST, '/about')).toBe(true);
		});

		it('should return true for admin accessing any route', () => {
			expect(canAccessRoute(UserRole.ADMIN, '/dashboard')).toBe(true);
			expect(canAccessRoute(UserRole.ADMIN, '/create-assistant')).toBe(true);
			expect(canAccessRoute(UserRole.ADMIN, '/voice-agents')).toBe(true);
			expect(canAccessRoute(UserRole.ADMIN, '/custom-demos')).toBe(true);
		});

		it('should return true for user accessing allowed routes', () => {
			expect(canAccessRoute(UserRole.USER, '/dashboard')).toBe(true);
			expect(canAccessRoute(UserRole.USER, '/create-assistant')).toBe(true);
			expect(canAccessRoute(UserRole.USER, '/voice-agents')).toBe(true);
			expect(canAccessRoute(UserRole.USER, '/custom-demos')).toBe(true);
		});

		it('should return false for demo user accessing restricted routes', () => {
			expect(canAccessRoute(UserRole.DEMO, '/create-assistant')).toBe(false);
		});

		it('should return true for demo user accessing allowed routes', () => {
			expect(canAccessRoute(UserRole.DEMO, '/custom-demos')).toBe(true);
		});

		it('should return false for guest accessing restricted routes', () => {
			expect(canAccessRoute(UserRole.GUEST, '/dashboard')).toBe(false);
			expect(canAccessRoute(UserRole.GUEST, '/create-assistant')).toBe(false);
			expect(canAccessRoute(UserRole.GUEST, '/voice-agents')).toBe(false);
		});

		it('should return true for guest accessing public routes', () => {
			expect(canAccessRoute(UserRole.GUEST, '/custom-demos')).toBe(true);
		});

		it('should return false for null role accessing protected routes', () => {
			expect(canAccessRoute(null, '/dashboard')).toBe(false);
			expect(canAccessRoute(null, '/create-assistant')).toBe(false);
		});
	});
});
