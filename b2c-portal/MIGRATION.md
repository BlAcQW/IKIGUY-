# Authentication Migration from Supabase to MongoDB

## Overview
The authentication system has been migrated from Supabase to MongoDB backend authentication. This migration provides better integration with the core backend and eliminates dependency on external services.

## Migration Status ✅ COMPLETED

### Main Application Flow - ✅ MIGRATED
- [x] **App.tsx** - Updated to use `MongoAuthProvider` instead of `AuthProvider`
- [x] **ProtectedRoute.tsx** - Updated to use `useMongoAuth` instead of `useAuth`
- [x] **core-api.ts** - Updated to use MongoDB JWT tokens instead of Supabase tokens
- [x] **Auth page** - Replaced with `MongoAuth.tsx` using MongoDB authentication

### New MongoDB Auth Components - ✅ CREATED
- [x] **MongoAuthContext.tsx** - New authentication context for MongoDB
- [x] **MongoLoginForm.tsx** - New login form using MongoDB backend
- [x] **MongoSignupForm.tsx** - New signup form using MongoDB backend
- [x] **MongoAuth.tsx** - New authentication page with tabs for login/signup
- [x] **mongo-auth.ts** - MongoDB authentication service client

### Deprecated Files - ✅ DEPRECATED
- [x] **Auth.deprecated.tsx** - Original Supabase auth page (deprecated)
- [x] **useAuth.deprecated.tsx** - Original Supabase auth hook (deprecated)
- [x] **AuthContext.deprecated.tsx** - Original Supabase auth context (deprecated)

### Components Using MongoDB Auth - ✅ COMPLETED
All main application components have been updated to use MongoDB authentication:
- [x] `components/audiences/CreateAudienceDialog.tsx`
- [x] `components/audiences/EditAudienceDialog.tsx`
- [x] `components/analytics/DeploymentAnalyticsDashboard.tsx`
- [x] `components/analytics/EnhancedAnalytics.tsx`
- [x] `components/analytics/AutomationMonitoringDashboard.tsx`
- [x] `components/dashboard/HelpdeskDashboard.tsx`
- [x] `components/voice-agent/CreateAssistantModal.tsx`
- [x] `hooks/useIndustryModules.ts`
- [x] `pages/admin/AdminLayout.tsx`
- [x] `pages/Automations.tsx`
- [x] `pages/SystemHealth.tsx`

## Migration Guide for Remaining Components

To update components that still use the deprecated `useAuth`:

1. **Replace the import:**
   ```typescript
   // OLD (deprecated)
   import { useAuth } from '@/hooks/useAuth';

   // NEW (MongoDB)
   import { useMongoAuth } from '@/components/auth/MongoAuthContext';
   ```

2. **Update the hook usage:**
   ```typescript
   // OLD (Supabase)
   const { user, session, loading } = useAuth();

   // NEW (MongoDB)
   const { user, isAuthenticated, isLoading, getTenantId } = useMongoAuth();
   ```

3. **Update user object access:**
   ```typescript
   // OLD (Supabase user structure)
   const userId = user?.id;
   const email = user?.email;

   // NEW (MongoDB user structure)
   const userId = user?.id;
   const email = user?.email;
   const tenantId = getTenantId(); // For organization/tenant context
   ```

## Backend Authentication Migration ✅ COMPLETED

The backend has been migrated to use MongoDB for authentication:
- JWT tokens are generated and validated by the core backend
- User and organization data stored in MongoDB
- Authentication endpoints: `/auth/signup`, `/auth/signin`, `/auth/signout`, `/auth/me`
- Health endpoint: `/auth/health`

## Testing Results ✅ VERIFIED

- ✅ MongoDB auth health endpoint responds correctly
- ✅ User signup creates account and organization
- ✅ User signin generates valid JWT tokens
- ✅ JWT tokens work with backend API endpoints
- ✅ Frontend builds without errors
- ✅ Main authentication flow works end-to-end

## Cleanup Tasks ⚠️ FUTURE WORK

1. ✅ Update remaining components to use `useMongoAuth` - COMPLETED
2. Remove deprecated `.deprecated.tsx` files after verification
3. Update test files to use MongoDB authentication
4. Remove Supabase dependencies from package.json if no longer needed

## Implementation Details

### MongoDB Auth Service Features
- Email/password authentication
- JWT token generation with proper claims
- Automatic organization creation
- Token refresh functionality
- Session management with localStorage
- Error handling with user-friendly messages

### Security Improvements
- JWT tokens issued by core backend (not external service)
- Organization-based multi-tenancy
- Proper token expiration and refresh
- Secure token storage in localStorage
- CORS and API timeout protection

## Notes
- The old Supabase authentication is completely bypassed in the main app flow
- Components using deprecated auth hooks will continue to work but should be updated
- All new development should use `useMongoAuth` and the MongoDB authentication system
- This migration eliminates external dependencies and provides better integration with the core backend