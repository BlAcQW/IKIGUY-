# KasaAI Core Backend API Documentation

## Overview

The KasaAI Core Backend provides a comprehensive REST API for user management, organization management, and authentication services. This API serves as the backbone for the KasaAI platform, supporting multi-tenant organizations with role-based access control.

## Base URL

- **Production**: `https://api.ailabsafrica.com`
- **Development**: `http://localhost:30027`

## Authentication

The API uses JWT (JSON Web Token) based authentication with access and refresh tokens.

### Token Types

- **Access Token**: Short-lived token (1 hour) for API access
- **Refresh Token**: Long-lived token (30 days) for obtaining new access tokens

### Authentication Header

```http
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/signup

Register a new user and create their default organization.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "display_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "Acme Corp"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "organization": {
    "id": "org_456",
    "name": "Acme Corp",
    "display_name": "Acme Corp",
    "description": "Default organization created during signup"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors
- `409 Conflict`: Email already exists
- `429 Too Many Requests`: Rate limit exceeded

#### POST /auth/signin

Authenticate an existing user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "display_name": "John Doe"
  },
  "organization": {
    "id": "org_456",
    "name": "Acme Corp"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account deactivated
- `423 Locked`: Account temporarily locked

#### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...},
  "organization": {...}
}
```

#### GET /auth/me

Get current authenticated user information.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "display_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "email_verified": true,
  "primary_organization_id": "org_456",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-15T10:30:00Z"
}
```

#### POST /auth/signout

Sign out current user and invalidate session.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully signed out"
}
```

### Organization Management Endpoints

#### GET /organizations

Get organizations for the current user.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "organizations": [
    {
      "id": "org_456",
      "name": "Acme Corp",
      "display_name": "Acme Corp",
      "description": "Technology company",
      "industry": "Technology",
      "website": "https://acme.com",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "user_role": "owner",
      "user_permissions": ["*"]
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

#### POST /organizations

Create a new organization.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "New Company",
  "display_name": "New Company Inc.",
  "description": "A new technology company",
  "industry": "Technology",
  "website": "https://newcompany.com"
}
```

**Response (201 Created):**
```json
{
  "id": "org_789",
  "name": "New Company",
  "display_name": "New Company Inc.",
  "description": "A new technology company",
  "industry": "Technology",
  "website": "https://newcompany.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /organizations/{org_id}

Get organization details.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID

**Response (200 OK):**
```json
{
  "id": "org_456",
  "name": "Acme Corp",
  "display_name": "Acme Corp",
  "description": "Technology company",
  "industry": "Technology",
  "website": "https://acme.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-10T15:20:00Z",
  "member_count": 5,
  "settings": {
    "allow_public_signup": false,
    "require_email_verification": true
  }
}
```

#### PUT /organizations/{org_id}

Update organization information.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID

**Request Body:**
```json
{
  "display_name": "Acme Corporation",
  "description": "Leading technology solutions provider",
  "website": "https://acmecorp.com"
}
```

**Response (200 OK):**
```json
{
  "id": "org_456",
  "name": "Acme Corp",
  "display_name": "Acme Corporation",
  "description": "Leading technology solutions provider",
  "website": "https://acmecorp.com",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### DELETE /organizations/{org_id}

Delete an organization (soft delete).

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID

**Response (200 OK):**
```json
{
  "message": "Organization deleted successfully"
}
```

**Error Responses:**
- `403 Forbidden`: Only owners can delete organizations
- `409 Conflict`: Cannot delete last organization for users

### Organization User Management

#### GET /organizations/{org_id}/users

Get users in an organization.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID

**Query Parameters:**
- `role` (optional): Filter by role
- `status` (optional): Filter by status (active/inactive)
- `search` (optional): Search by name or email
- `page` (optional): Page number
- `limit` (optional): Items per page

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "user_123",
      "user_id": "user_123",
      "email": "user@example.com",
      "display_name": "John Doe",
      "role": "owner",
      "is_active": true,
      "joined_at": "2024-01-01T00:00:00Z",
      "permissions": {}
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

#### POST /organizations/{org_id}/users/invite

Invite a user to join an organization.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "role": "member",
  "message": "Welcome to our organization!"
}
```

**Response (201 Created):**
```json
{
  "id": "inv_789",
  "email": "newuser@example.com",
  "role": "member",
  "status": "pending",
  "expires_at": "2024-01-22T10:30:00Z",
  "invitation_url": "https://app.kasaai.com/invite/abc123"
}
```

#### PUT /organizations/{org_id}/users/{user_id}

Update user role or permissions in organization.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID
- `user_id`: User ID

**Request Body:**
```json
{
  "role": "admin",
  "permissions": {
    "manage_campaigns": true,
    "view_analytics": true
  }
}
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "role": "admin",
  "permissions": {
    "manage_campaigns": true,
    "view_analytics": true
  },
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### DELETE /organizations/{org_id}/users/{user_id}

Remove user from organization.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `org_id`: Organization ID
- `user_id`: User ID

**Response (200 OK):**
```json
{
  "message": "User removed from organization successfully"
}
```

### Admin Endpoints

#### GET /admin/users

Get all users (admin only).

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `search` (optional): Search by email or name
- `role` (optional): Filter by role
- `status` (optional): Filter by status
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-15T10:30:00Z",
      "email_verified": true,
      "organization_id": "org_456",
      "organization_name": "Acme Corp"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

#### POST /admin/users

Create a new user (admin only).

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "email": "admin@example.com",
  "name": "Admin User",
  "password": "SecurePassword123!",
  "role": "admin",
  "sendWelcomeEmail": true
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "user": {
    "id": "user_456",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin",
    "organization_id": "org_789",
    "organization_name": "Admin User's Organization"
  }
}
```

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "code": "AUTH001",
  "message": "Invalid email or password",
  "details": {
    "field": "password",
    "attempts_remaining": 3
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

#### Authentication Errors (AUTH)
- `AUTH001`: Invalid credentials
- `AUTH002`: Account locked
- `AUTH003`: Email not verified
- `AUTH004`: Token expired
- `AUTH005`: Token invalid
- `AUTH006`: Session expired
- `AUTH007`: Weak password
- `AUTH008`: Email already exists
- `AUTH009`: Rate limit exceeded

#### Organization Errors (ORG)
- `ORG001`: Organization not found
- `ORG002`: Access denied
- `ORG003`: Organization already exists
- `ORG004`: Member limit exceeded
- `ORG005`: Invalid role
- `ORG006`: Owner required
- `ORG007`: Cannot delete last owner

#### User Errors (USER)
- `USER001`: User not found
- `USER002`: User already exists
- `USER003`: User inactive
- `USER004`: Permission denied
- `USER005`: Invalid user data

#### Database Errors (DB)
- `DB001`: Connection error
- `DB002`: Operation failed
- `DB003`: Constraint violation
- `DB004`: Timeout

#### Validation Errors (VAL)
- `VAL001`: Validation failed
- `VAL002`: Invalid email format
- `VAL003`: Invalid password format
- `VAL004`: Required field missing

## Rate Limiting

API endpoints are protected by rate limiting to prevent abuse:

- **Authentication endpoints**: 5 requests per minute per IP
- **General API endpoints**: 100 requests per minute per user
- **Admin endpoints**: 50 requests per minute per admin user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Pagination

List endpoints support pagination with these query parameters:

- `page`: Page number (default: 1)
- `limit`/`per_page`: Items per page (default: 20, max: 100)

Pagination response includes:

```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

## Data Models

### User Model

```json
{
  "id": "string",
  "email": "string",
  "display_name": "string",
  "first_name": "string",
  "last_name": "string",
  "avatar_url": "string",
  "is_active": "boolean",
  "email_verified": "boolean",
  "primary_organization_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_login_at": "datetime",
  "login_count": "number"
}
```

### Organization Model

```json
{
  "id": "string",
  "name": "string",
  "display_name": "string",
  "description": "string",
  "industry": "string",
  "website": "string",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### OrganizationUser Model

```json
{
  "id": "string",
  "organization_id": "string",
  "user_id": "string",
  "email": "string",
  "display_name": "string",
  "role": "owner|admin|manager|member|viewer",
  "is_active": "boolean",
  "joined_at": "datetime",
  "permissions": "object"
}
```

## Role-Based Permissions

### Role Hierarchy

1. **Universal Admin**: Cross-organization access, system management
2. **Owner**: Full organization control, billing, user management
3. **Admin**: User management, settings, campaigns, analytics
4. **Manager**: Campaign management, analytics, view users
5. **Member**: Basic content creation, view campaigns
6. **Viewer**: Read-only access to campaigns and basic analytics

### Permission Matrix

| Permission | Universal Admin | Owner | Admin | Manager | Member | Viewer |
|-----------|----------------|-------|--------|---------|--------|--------|
| manage_users | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| manage_settings | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| manage_billing | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| manage_campaigns | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| create_campaigns | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| view_campaigns | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| view_analytics | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| manage_integrations | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

## Security Best Practices

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
- No common weak patterns

### Token Security

- Access tokens expire in 1 hour
- Refresh tokens expire in 30 days
- Tokens are revoked on sign out
- Session tracking by device/IP

### API Security

- HTTPS only in production
- Rate limiting per endpoint
- Input validation and sanitization
- SQL injection prevention
- CORS protection

## SDKs and Integration

### JavaScript/TypeScript SDK

```javascript
import { KasaAIClient } from '@kasaai/sdk';

const client = new KasaAIClient({
  apiUrl: 'https://api.ailabsafrica.com',
  accessToken: 'your-access-token'
});

// Authenticate
const auth = await client.auth.signin({
  email: 'user@example.com',
  password: 'password'
});

// Get organizations
const orgs = await client.organizations.list();
```

### Python SDK

```python
from kasaai_sdk import KasaAIClient

client = KasaAIClient(
    api_url='https://api.ailabsafrica.com',
    access_token='your-access-token'
)

# Authenticate
auth = client.auth.signin(
    email='user@example.com',
    password='password'
)

# Get organizations
orgs = client.organizations.list()
```

## Support

For API support and questions:

- **Documentation**: [https://docs.kasaai.com](https://docs.kasaai.com)
- **Status Page**: [https://status.kasaai.com](https://status.kasaai.com)
- **Email Support**: [api-support@ailabsafrica.com](mailto:api-support@ailabsafrica.com)

## Changelog

### v1.2.0 (Latest)
- Enhanced error handling with standardized error codes
- Improved rate limiting
- Added organization user management endpoints
- Enhanced security features

### v1.1.0
- Added organization management
- Role-based access control
- Admin endpoints

### v1.0.0
- Initial API release
- Basic authentication
- User management