# Supabase to MongoDB Migration Plan

## Overview
This document outlines the strategy for migrating from the current hybrid Supabase/MongoDB authentication system to a pure MongoDB-based user management system.

## Current State Analysis

### Supabase Dependencies
- User authentication and session management
- Admin user management endpoints (`/api/admin/users`)
- Password reset functionality
- Email verification
- JWT token generation

### MongoDB Current Usage
- User profiles and extended data
- Organization management
- Role-based permissions
- Session tracking
- Invitation system

## Migration Strategy

### Phase 1: Enhanced MongoDB Auth Service
**Timeline: 1-2 weeks**

#### 1.1 Password Reset System
```python
# New methods to add to AuthService
async def initiate_password_reset(self, email: str) -> dict
async def verify_reset_token(self, token: str) -> dict
async def complete_password_reset(self, token: str, new_password: str) -> dict
```

#### 1.2 Email Verification System
```python
# New methods to add to AuthService
async def send_verification_email(self, user_id: str) -> dict
async def verify_email(self, verification_token: str) -> dict
async def resend_verification_email(self, email: str) -> dict
```

#### 1.3 Enhanced JWT Token Management
```python
# Enhanced token methods
async def generate_access_token(self, user_id: str, additional_claims: dict = None) -> str
async def generate_refresh_token(self, user_id: str) -> str
async def validate_token(self, token: str) -> dict
async def revoke_token(self, token: str) -> bool
async def revoke_all_user_tokens(self, user_id: str) -> bool
```

### Phase 2: Admin System Migration
**Timeline: 1 week**

#### 2.1 Replace Supabase Admin Endpoints
- Migrate `/api/admin/users` to pure MongoDB
- Remove Supabase client dependencies
- Update admin privilege checking

#### 2.2 Enhanced User Management
```python
# Enhanced admin methods
async def get_all_users_paginated(self, filters: dict, page: int, limit: int) -> dict
async def create_admin_user(self, user_data: dict) -> dict
async def update_user_admin(self, user_id: str, updates: dict) -> dict
async def deactivate_user(self, user_id: str) -> bool
async def reactivate_user(self, user_id: str) -> bool
```

### Phase 3: Email Service Integration
**Timeline: 1 week**

#### 3.1 Email Service Implementation
```python
# New email service
class EmailService:
    async def send_verification_email(self, email: str, token: str) -> bool
    async def send_password_reset_email(self, email: str, token: str) -> bool
    async def send_welcome_email(self, email: str, name: str) -> bool
    async def send_invitation_email(self, email: str, org_name: str, token: str) -> bool
```

#### 3.2 Email Templates
- Verification email template
- Password reset email template
- Welcome email template
- Organization invitation template

### Phase 4: Authentication Middleware Update
**Timeline: 3-5 days**

#### 4.1 JWT Middleware Enhancement
```python
# Enhanced authentication dependency
async def get_current_user_jwt(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Pure MongoDB JWT authentication dependency
    Replaces get_current_user_mongo with enhanced validation
    """
```

#### 4.2 Route Protection Updates
- Update all protected routes to use new JWT middleware
- Remove Supabase token validation
- Enhance permission checking

### Phase 5: Data Migration Scripts
**Timeline: 1 week**

#### 5.1 User Data Migration
```python
# Migration script for existing Supabase users
async def migrate_supabase_users_to_mongodb():
    """
    Migrate all existing Supabase users to MongoDB
    - Preserve user IDs for consistency
    - Migrate user metadata
    - Create corresponding organizations
    - Set up proper roles and permissions
    """
```

#### 5.2 Session Migration
```python
async def migrate_active_sessions():
    """
    Migrate active Supabase sessions to MongoDB
    - Convert Supabase JWT to MongoDB JWT
    - Preserve session expiry times
    - Update device tracking
    """
```

## Technical Implementation Details

### Enhanced MongoDB Schema

#### Users Collection
```javascript
{
  "_id": ObjectId,
  "id": "uuid", // Keep consistent with Supabase IDs
  "email": "string",
  "password_hash": "string", // bcrypt hash
  "email_verified": boolean,
  "email_verification_token": "string",
  "email_verification_expires": Date,
  "password_reset_token": "string",
  "password_reset_expires": Date,
  "display_name": "string",
  "first_name": "string",
  "last_name": "string",
  "avatar_url": "string",
  "is_active": boolean,
  "last_login_at": Date,
  "login_count": Number,
  "created_at": Date,
  "updated_at": Date,
  // Enhanced fields
  "failed_login_attempts": Number,
  "locked_until": Date,
  "requires_password_change": boolean,
  "last_password_change": Date
}
```

#### JWT Tokens Collection
```javascript
{
  "_id": ObjectId,
  "token_id": "uuid",
  "user_id": "string",
  "token_type": "access" | "refresh",
  "token_hash": "string", // Hash of the actual token
  "expires_at": Date,
  "created_at": Date,
  "is_revoked": boolean,
  "device_info": {
    "user_agent": "string",
    "ip_address": "string",
    "device_id": "string"
  }
}
```

### Security Enhancements

#### Rate Limiting Implementation
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")
async def signin_endpoint():
    """Limited to 5 login attempts per minute per IP"""

@limiter.limit("3/minute")
async def password_reset_endpoint():
    """Limited to 3 password reset requests per minute per IP"""
```

#### Enhanced Password Security
```python
class PasswordPolicy:
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PREVENT_COMMON_PASSWORDS = True

    @staticmethod
    def validate_password(password: str) -> dict:
        """Comprehensive password validation"""
```

## Migration Timeline

| Phase | Duration | Dependencies | Risk Level |
|-------|----------|--------------|------------|
| Phase 1: Enhanced MongoDB Auth | 1-2 weeks | Email service setup | Medium |
| Phase 2: Admin System Migration | 1 week | Phase 1 complete | Low |
| Phase 3: Email Service Integration | 1 week | Email provider setup | Medium |
| Phase 4: Auth Middleware Update | 3-5 days | Phase 1-3 complete | High |
| Phase 5: Data Migration | 1 week | All phases complete | High |

**Total Timeline: 5-6 weeks**

## Risk Mitigation

### High-Risk Areas
1. **Authentication Middleware Update**: Could break all protected endpoints
   - **Mitigation**: Feature flag implementation, gradual rollout

2. **Data Migration**: Risk of data loss or corruption
   - **Mitigation**: Comprehensive backup strategy, rollback plan

3. **Email Service Integration**: Risk of email delivery issues
   - **Mitigation**: Multiple email provider fallbacks, monitoring

### Rollback Strategy
1. Keep Supabase configuration available during transition
2. Feature flags for switching between systems
3. Data synchronization scripts for rollback scenarios
4. Monitoring and alerting for authentication failures

## Testing Strategy

### Unit Tests
- [ ] Enhanced auth service methods
- [ ] Email service functionality
- [ ] JWT token management
- [ ] Password policy validation

### Integration Tests
- [ ] End-to-end authentication flow
- [ ] Password reset workflow
- [ ] Email verification process
- [ ] Admin user management

### Load Tests
- [ ] Authentication endpoint performance
- [ ] JWT token validation speed
- [ ] Database query optimization
- [ ] Concurrent user sessions

## Success Metrics

### Performance Metrics
- Authentication response time < 100ms
- JWT validation < 50ms
- Password reset flow completion < 2 minutes
- Email delivery rate > 99%

### Security Metrics
- Zero authentication bypass incidents
- Failed login attempt detection 100%
- Password policy compliance 100%
- Token revocation effectiveness 100%

### User Experience Metrics
- Login success rate > 99%
- Password reset success rate > 95%
- Email verification completion > 90%
- User support tickets reduction 50%

## Post-Migration Cleanup

1. Remove all Supabase dependencies from codebase
2. Archive Supabase configuration and credentials
3. Update documentation and API specs
4. Clean up deprecated endpoints
5. Update deployment scripts and CI/CD pipelines

## Conclusion

This migration plan provides a comprehensive strategy for transitioning from Supabase to a pure MongoDB authentication system. The phased approach minimizes risk while ensuring feature parity and enhanced security. The timeline allows for thorough testing and gradual rollout to ensure system stability.

## Next Steps

1. **Immediate**: Set up development environment for testing
2. **Week 1**: Begin Phase 1 implementation
3. **Week 2**: Complete enhanced MongoDB auth service
4. **Week 3**: Implement admin system migration
5. **Week 4**: Email service integration
6. **Week 5**: Authentication middleware update
7. **Week 6**: Data migration and final testing