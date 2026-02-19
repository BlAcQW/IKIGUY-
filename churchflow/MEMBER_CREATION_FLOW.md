# Member Creation Flow

This document describes how members are created in the ChurchFlow system, from visitors to active members.

## Overview

The member creation flow follows this progression:

1. **Visitor** → Initial capture of someone visiting the church
2. **First Timer** → Visitor is registered as a first-time attendee
3. **Member** → First timer or visitor is converted to an active member

## Path 1: Visitor → Member

### Step 1: Capture Visitor
- **Route**: `/visitors` (Visitor Capture page)
- **Action**: Admin captures visitor information
- **Service**: `VisitorService.capture_visitor()`
- **Creates**: User with `member_status: "visitor"` and `current_spiritual_stage: "first_timer"`

### Step 2: Convert to Member
- **Route**: Visitor Detail page → Convert to Member action
- **Action**: Admin converts visitor to active member
- **Service**: `UserService.transition_to_member()`
- **Updates**: 
  - `member_status: "active_member"`
  - Assigns `branch_id`
  - Updates `current_spiritual_stage` to "new_convert" if still first/second timer

## Path 2: First Timer → Member

### Step 1: Register First Timer
- **Route**: `/admin/first-timers` (First Timer Dashboard)
- **Action**: Admin registers first-time visitor
- **Service**: `FirstTimerService.create_first_timer()`
- **Creates**: FirstTimer record (separate collection)

### Step 2: Convert First Timer to Member
- **Route**: First Timer Dashboard → Convert to Member action
- **Action**: Admin converts first timer to member
- **Service**: `FirstTimerService.convert_to_member()`
- **Process**:
  1. Checks if user exists by phone/email
  2. Creates new User if doesn't exist, or links to existing User
  3. Transfers first timer data to User profile
  4. Marks first timer as converted
  5. Sets `member_status: "active_member"`

## Path 3: Direct Member Creation

Members can also be created directly through:
- **Member Portal** → Admin tab (if admin)
- User registration flows
- Data migration/import scripts

## Key Models

### User Model (`app/models/user.py`)
- `member_status`: "visitor" | "active_member" | "inactive_member" | "alumni"
- `current_spiritual_stage`: "first_timer" | "new_convert" | etc.
- `branch_id`: Assigned branch (for members)

### FirstTimer Model (`app/models/first_timer.py`)
- Separate collection for tracking first-time visitors
- Can be converted to User
- `converted_to_member`: Boolean flag
- `member_id`: Reference to User if converted

## Admin Interfaces

### 1. Visitor Capture (`/visitors`)
- Quick capture form for visitors
- Creates User with visitor status

### 2. First Timer Dashboard (`/admin/first-timers`)
- Manage first-time visitors
- Convert to members
- Track follow-ups

### 3. Member Portal - Admin Tab (`/portal` → Admin tab)
- Comprehensive member analytics
- Member management (for admins)
- Statistics and demographics

### 4. Members Dashboard (`/admin/members`) - **DEPRECATED**
- ⚠️ This route has been removed
- Functionality moved to Member Portal Admin tab
- Use `/portal` → Admin tab instead

## API Endpoints

### Visitor Capture
- `POST /api/v1/visitors` - Capture visitor

### First Timers
- `POST /api/v1/first-timers` - Create first timer
- `POST /api/v1/first-timers/{id}/convert-to-member` - Convert to member

### Members
- `GET /api/v1/member-analytics` - Get member statistics
- `PUT /api/v1/users/{id}/transition-to-member` - Transition visitor to member

## Best Practices

1. **Always capture visitors first** before converting to members
2. **Use First Timer system** for systematic follow-up
3. **Assign branch_id** when converting to member
4. **Track journey stages** for discipleship purposes
5. **Use Member Portal Admin tab** for member management (not `/admin/members`)

