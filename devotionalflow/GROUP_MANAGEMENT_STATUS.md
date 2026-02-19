# Group Management CRUD Status Report

## Overview
This document outlines the current state of group management functionality including CRUD operations, join/leave, and invite features.

---

## ✅ CREATE - IMPLEMENTED

### Backend
- **Service Function**: `create_group(group_data, creator_id)` in `group_service.py`
- **API Endpoint**: `POST /api/v1/groups`
- **Features**:
  - Create group with name, description
  - Set privacy (public/private)
  - Link to devotional (optional)
  - Set discussion topic (optional)
  - Creator automatically added as admin member
  - Returns created group with full details

### Frontend
- ❌ **NOT IMPLEMENTED** - No create group page or form

---

## ✅ READ - IMPLEMENTED

### Backend
- **Service Functions**:
  - `get_group_by_id(group_id)` - Get single group
  - `list_groups(page, page_size, is_public, search)` - List groups with filters
- **API Endpoints**:
  - `GET /api/v1/groups` - List groups (supports pagination, search, public/private filter)
  - `GET /api/v1/groups/{id}` - Get group details
- **Features**:
  - Pagination support
  - Search by name or description
  - Filter by public/private
  - Returns group with members list

### Frontend
- ❌ **NOT IMPLEMENTED** - No groups browse page or group detail page

---

## ❌ UPDATE - MISSING

### Backend
- **Model Exists**: `GroupUpdate` model in `group.py` with fields:
  - `name` (optional)
  - `description` (optional)
  - `is_public` (optional)
  - `discussion_topic` (optional)
- **Service Function**: ❌ **MISSING** - No `update_group()` function
- **API Endpoint**: ❌ **MISSING** - No `PUT /api/v1/groups/{id}` or `PATCH /api/v1/groups/{id}`

### Frontend
- ❌ **NOT IMPLEMENTED** - No group settings/edit page

**What's Needed:**
1. `update_group(group_id, group_data, user_id)` service function
2. `PUT /api/v1/groups/{id}` API endpoint
3. Authorization check (only creator/admin can update)
4. Frontend edit group page

---

## ❌ DELETE - MISSING

### Backend
- **Service Function**: ❌ **MISSING** - No `delete_group()` function
- **API Endpoint**: ❌ **MISSING** - No `DELETE /api/v1/groups/{id}`

### Frontend
- ❌ **NOT IMPLEMENTED** - No delete group functionality

**What's Needed:**
1. `delete_group(group_id, user_id)` service function
2. `DELETE /api/v1/groups/{id}` API endpoint
3. Authorization check (only creator can delete)
4. Option to transfer ownership before deletion
5. Frontend delete confirmation dialog

---

## ✅ JOIN - IMPLEMENTED

### Backend
- **Service Function**: `join_group(group_id, user_id)` in `group_service.py`
- **API Endpoint**: `POST /api/v1/groups/{id}/join`
- **Features**:
  - Validates group exists
  - Checks if already a member
  - Adds user as member with role "member"
  - Increments members_count
  - Returns updated group

### Frontend
- ❌ **NOT IMPLEMENTED** - No UI to join groups

---

## ✅ LEAVE - IMPLEMENTED

### Backend
- **Service Function**: `leave_group(group_id, user_id)` in `group_service.py`
- **API Endpoint**: `POST /api/v1/groups/{id}/leave`
- **Features**:
  - Validates group exists
  - Prevents creator from leaving (must transfer ownership or delete)
  - Removes user from members list
  - Decrements members_count

### Frontend
- ❌ **NOT IMPLEMENTED** - No UI to leave groups

---

## ❌ INVITE - MISSING

### Backend
- **Invite System**: ❌ **COMPLETELY MISSING**
  - No invite model/schema
  - No invite link generation
  - No invite acceptance endpoint
  - No invite management

### Frontend
- ❌ **NOT IMPLEMENTED** - No invite functionality

**What's Needed:**
1. **Invite Model**:
   - `invite_id`, `group_id`, `inviter_id`, `invitee_email` (or `invitee_id`)
   - `invite_token` (for link-based invites)
   - `status` (pending, accepted, declined, expired)
   - `expires_at`, `created_at`

2. **Service Functions**:
   - `create_invite(group_id, inviter_id, invitee_email)` - Create invite
   - `get_invite_by_token(token)` - Get invite by token
   - `accept_invite(token, user_id)` - Accept invite
   - `decline_invite(invite_id)` - Decline invite
   - `list_group_invites(group_id)` - List pending invites
   - `revoke_invite(invite_id, user_id)` - Revoke invite

3. **API Endpoints**:
   - `POST /api/v1/groups/{id}/invites` - Create invite
   - `GET /api/v1/groups/{id}/invites` - List invites
   - `POST /api/v1/invites/{token}/accept` - Accept invite
   - `POST /api/v1/invites/{invite_id}/decline` - Decline invite
   - `DELETE /api/v1/invites/{invite_id}` - Revoke invite

4. **Frontend**:
   - Invite button on group page
   - Invite form (email input)
   - Invite link generation and sharing
   - Invite acceptance page
   - Pending invites list

---

## Summary Table

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| **Create Group** | ✅ | ❌ | Backend ready, needs UI |
| **Read Groups** | ✅ | ❌ | Backend ready, needs UI |
| **Update Group** | ❌ | ❌ | Missing both |
| **Delete Group** | ❌ | ❌ | Missing both |
| **Join Group** | ✅ | ❌ | Backend ready, needs UI |
| **Leave Group** | ✅ | ❌ | Backend ready, needs UI |
| **Invite Users** | ❌ | ❌ | Missing both |

---

## Current Backend API Endpoints

### Implemented
- `POST /api/v1/groups` - Create group ✅
- `GET /api/v1/groups` - List groups ✅
- `GET /api/v1/groups/{id}` - Get group ✅
- `POST /api/v1/groups/{id}/join` - Join group ✅
- `POST /api/v1/groups/{id}/leave` - Leave group ✅
- `POST /api/v1/groups/{id}/messages` - Create message ✅
- `GET /api/v1/groups/{id}/messages` - List messages ✅

### Missing
- `PUT /api/v1/groups/{id}` - Update group ❌
- `DELETE /api/v1/groups/{id}` - Delete group ❌
- `POST /api/v1/groups/{id}/invites` - Create invite ❌
- `GET /api/v1/groups/{id}/invites` - List invites ❌
- `POST /api/v1/invites/{token}/accept` - Accept invite ❌
- `POST /api/v1/invites/{invite_id}/decline` - Decline invite ❌
- `DELETE /api/v1/invites/{invite_id}` - Revoke invite ❌

---

## Recommendations

### Priority 1: Complete CRUD Operations
1. Implement `update_group()` service function
2. Add `PUT /api/v1/groups/{id}` endpoint
3. Implement `delete_group()` service function
4. Add `DELETE /api/v1/groups/{id}` endpoint
5. Add authorization checks (only creator/admin can update/delete)

### Priority 2: Invite System
1. Create invite model and database schema
2. Implement invite service functions
3. Add invite API endpoints
4. Generate invite links with tokens
5. Email invite functionality (optional)

### Priority 3: Frontend Implementation
1. Create Groups browse page (`/groups`)
2. Create group detail page (`/groups/:id`)
3. Create group form (`/groups/new`)
4. Group settings/edit page
5. Invite UI components

---

## Files to Create/Update

### Backend - New Files
- `backend/app/models/invite.py` - Invite models
- `backend/app/services/invite_service.py` - Invite service functions
- `backend/app/routes/invites.py` - Invite API routes

### Backend - Files to Update
- `backend/app/services/group_service.py` - Add `update_group()` and `delete_group()`
- `backend/app/routes/groups.py` - Add update and delete endpoints

### Frontend - New Files
- `frontend/src/pages/Groups.tsx` - Groups browse page
- `frontend/src/pages/GroupDetail.tsx` - Group detail page
- `frontend/src/pages/CreateGroup.tsx` - Create group page
- `frontend/src/pages/GroupSettings.tsx` - Group settings/edit page
- `frontend/src/components/groups/InviteDialog.tsx` - Invite dialog component

### Frontend - Files to Update
- `frontend/src/lib/api.ts` - Add group API methods
- `frontend/src/App.tsx` - Add group routes
- `frontend/src/components/navigation/MainNavigation.tsx` - Add Groups link

---

**Last Updated**: 2024-12-19
**Status**: Backend has Create, Read, Join, Leave. Missing Update, Delete, and entire Invite system. Frontend completely missing.

