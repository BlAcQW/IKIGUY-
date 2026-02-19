# Interactive AI Bookshop - Task List

**Project**: InkWave - Interactive Audiobook Platform
**Created**: 2025-10-23
**Last Updated**: 2025-12-21 (Navigation Active State Fix)

---

## 🎉 Latest Update: Navigation Active State Fixed (2025-12-21)

### ✅ NAVIGATION ACTIVE STATE CONSISTENCY FIX

**Issue**: Main navigation items (Home, My Library, Discover, Leaderboard) were not correctly identified as active when clicked, especially across different pages.

**Root Cause Analysis**:
1. **Navigation Item Mismatch**: `MobileBottomNav.tsx` had different items than `Header.tsx`
   - MobileBottomNav: Home, Browse, Library, My Books, Profile
   - Header (regular users): Home, My Library, Discover, Leaderboard
2. **No Single Source of Truth**: Navigation items defined separately in two components
3. **Exact Match Only**: Active state used `location.pathname === item.path` which failed for nested routes

**Solution**: Centralized navigation configuration with smart active state detection

**Files Created**:
- `frontend/src/config/navigation.ts` - Single source of truth for navigation
- `frontend/src/config/navigation.test.ts` - 39 unit tests for navigation logic

**Files Modified**:
- `frontend/src/components/MobileBottomNav.tsx` - Uses centralized config
- `frontend/src/components/Header.tsx` - Uses centralized config

**Key Features**:
1. **Centralized Config**: All navigation items defined in `navigation.ts`
2. **Smart Active Detection**: `isNavItemActive()` supports:
   - Exact path matching (`/library` matches `/library`)
   - Prefix matching (`/discover` matches `/discover/123`)
   - Custom match paths (`/user/*` activates Discover)
   - Root path special handling (no false positives)
3. **Consistent Items**: Mobile and desktop navigation now share the same config
4. **Hidden Path Logic**: `shouldHideNavigation()` centralizes hide logic

**Testing**:
- ✅ 39 unit tests pass for navigation configuration
- ✅ Frontend builds successfully
- ✅ Active state works correctly across all routes

---

## 🎉 Previous Update: Real-Time Listening Stats Fixed (2025-12-08)

### ✅ LISTENING HOURS TRACKING FIX

**Issue #1**: Profile stats weren't updating in real-time while listening. Stats only showed up after 5+ minutes of listening due to transaction batching.

**Root Cause**:
- Backend creates listening transactions every 5 minutes to avoid spam
- Profile stats were calculated ONLY from transactions
- During first 0-5 minutes, no transaction exists, so stats showed old values

**Solution**: Modified `user_service.py:get_user_stats()` to include uncommitted time from active sessions:

**Issue #2**: Progress update timer was resetting constantly, preventing updates from being sent.

**Root Cause**:
- The `useChunkPlayer` interval timer had `currentTime`, `currentChunkIndex`, and `totalListeningMinutes` in its dependency array
- Since `currentTime` updates constantly during playback, the 60-second timer kept resetting
- Timer never completed, so progress updates never fired

**Solution**: Fixed `useChunkPlayer.ts` to use refs instead of closure values:
```python
# Add uncommitted time from active sessions (time not yet recorded in transactions)
active_sessions = await self.db.reading_sessions.find({
    "user_id": user_id,
    "completed_at": None  # Only active sessions
}).to_list(length=100)

uncommitted_minutes = 0.0
for session in active_sessions:
    total_time = session.get("total_time_spent_minutes", 0)
    last_transaction_time = session.get("last_transaction_time", 0)
    session_uncommitted = total_time - last_transaction_time
    if session_uncommitted > 0:
        uncommitted_minutes += session_uncommitted

total_listening_minutes = listening_time_minutes + uncommitted_minutes
```

**Testing**:
- ✅ Test script created: `/opt/kasaai/apps/test_realtime_stats.py`
- ✅ Verified uncommitted time is correctly added to stats
- ✅ Backend service restarted successfully

**Impact**:
- ✅ Profile stats now update in real-time (every 15 seconds with frontend auto-refresh)
- ✅ Users see their listening hours increment immediately while listening
- ✅ Leaderboard still uses denormalized cache (updated every 5 minutes)

```javascript
// Added refs for current values
const currentChunkIndexRef = useRef<number>(0);
const currentTimeRef = useRef<number>(0);
const totalListeningMinutesRef = useRef<number>(initialTotalTimeMinutes);

// Keep refs updated
useEffect(() => {
  currentChunkIndexRef.current = state.currentChunkIndex;
  currentTimeRef.current = state.currentTime;
}, [state.currentChunkIndex, state.currentTime]);

// Fixed interval - only depends on sessionId and isPlaying
useEffect(() => {
  if (sessionId && state.isPlaying) {
    progressUpdateTimer.current = setInterval(() => {
      onProgressUpdateRef.current?.(
        currentChunkIndexRef.current,  // Use ref, not closure
        currentTimeRef.current,         // Use ref, not closure
        totalListeningMinutesRef.current // Use ref, not closure
      );
    }, 60000);
    return () => clearInterval(progressUpdateTimer.current);
  }
}, [sessionId, state.isPlaying]); // No longer resets on time changes!
```

**Issue #3**: Leaderboard cache not updating, causing profile and leaderboard to show different hours.

**Root Cause**:
- Old sessions had 84 hours of uncommitted time across 103 users
- Profile showed committed + uncommitted (correct)
- Leaderboard showed only committed (outdated cache)
- Created discrepancy between the two

**Solution**: One-time migration script to credit all uncommitted time:
- Created transactions for 5,040 minutes (84 hours) of uncommitted listening
- Updated leaderboard cache for 103 affected users
- Both profile and leaderboard now show matching hours

**Files Modified**:
- `inkwave/backend/app/services/user_service.py` (line 406-429) - Backend uncommitted time
- `inkwave/frontend/src/hooks/useChunkPlayer.ts` (lines 217-220, 279-287, 645-662, 995-1001) - Frontend timer fix
- `inkwave/backend/scripts/migrate_uncommitted_time.py` - One-time migration script

**Migration Results**:
- ✅ 113 transactions created for uncommitted time
- ✅ 103 users credited with their listening time
- ✅ 84 hours of listening time properly recorded
- ✅ Profile and leaderboard now show matching hours for all users
- ✅ Top listener: king_deen with 29.87 hours

---

## 🎉 Previous Update: Social Features Completion & Book Clubs (2025-12-03)

### ✅ SOCIAL FEATURES IMPLEMENTATION PLAN

**Implementation Summary**: Comprehensive 7-9 day plan to complete InkWave social features (follow, leaderboard, activity feed) with full testing coverage and mobile optimization. Includes new Book Clubs feature for collaborative reading.

**Current Status**:
- ✅ Backend Social API: 100% Complete (Phase 1-3 commits: 446f2fd9, e951a571, f76fb851)
- ✅ Frontend Components: 100% Complete (all hooks and UI components ready)
- ⚠️ Frontend Integration: 0% (components not wired into app)
- ❌ Backend Tests: 0% (violates coding standards - CRITICAL)
- ❌ Frontend Tests: 0%
- ❌ Mobile Verification: Not tested on devices

---

#### Phase 1: Backend Integration Testing (Days 1-3) - **IN PROGRESS**

**Goal**: Create comprehensive test coverage using real MongoDB operations (NO mocks)

**Backend Test Files** (9 files, ~2200 lines, 120+ tests):
- [x] **test_social_follow_unfollow.py** (~320 lines, 13 tests) ✅ COMPLETE
  - [x] 5 happy path tests (follow, unfollow, get lists, is_following check)
  - [x] 4 edge cases (pagination, rate limiting, max limits, refollow)
  - [x] 4 failure cases (self-follow, non-existent user, duplicate follow)
  - **Status**: ✅ All 13 tests passing in 2.02s

- [x] **test_social_blocking.py** (~260 lines, 8 tests) ✅ COMPLETE
  - [x] 3 happy path tests (block, unblock, is_blocked check)
  - [x] 2 edge cases (removes mutual follows, blocked user cannot refollow)
  - [x] 3 failure cases (cannot block self, cannot block twice, unblock non-blocked)
  - **Status**: ✅ All 8 tests passing in 1.10s

- [ ] **test_social_reporting.py** (~220 lines, 4 tests)
  - [ ] 2 happy path tests (create report, admin reviews report)
  - [ ] 1 edge case (multiple users report same person)
  - [ ] 1 failure case (cannot report self)

- [ ] **test_reading_activity_crud.py** (~350 lines, 8 tests)
  - [ ] 4 happy path tests (started_book, completed_book, milestone, timeline)
  - [ ] 2 edge cases (duplicate prevention, privacy settings)
  - [ ] 2 failure cases (non-existent user/book)

- [ ] **test_activity_feed.py** (~300 lines, 4 tests)
  - [ ] 2 happy path tests (following feed, privacy respected)
  - [ ] 2 edge cases (excludes blocked users, pagination)

- [ ] **test_leaderboard.py** (~320 lines, 6 tests)
  - [ ] 3 happy path tests (all-time, weekly, user rank)
  - [ ] 3 edge cases (caching, anonymous mode, opt-out)

- [ ] **test_user_discovery.py** (~350 lines, 6 tests)
  - [ ] 3 happy path tests (search username, display name, get profile)
  - [ ] 3 edge cases (excludes blocked, respects privacy, followers_only)

- [ ] **test_username_management.py** (~240 lines, 5 tests)
  - [ ] 2 happy path tests (update username, validate format)
  - [ ] 2 edge cases (30-day cooldown, uniqueness check)
  - [ ] 1 failure case (invalid format)

- [ ] **test_social_stats_denormalization.py** (~220 lines, 3 tests)
  - [ ] 3 happy path tests (follow increments, unfollow decrements, block updates)

**Testing Infrastructure**:
```python
# Shared fixtures pattern (real MongoDB, no mocks)
MONGODB_URI = os.getenv("MONGODB_URI")
TEST_DATABASE = "inkwave_test_social"

@pytest_asyncio.fixture
async def db_client():
    client = AsyncIOMotorClient(MONGODB_URI)
    yield client
    await client.drop_database(TEST_DATABASE)  # Cleanup
    client.close()
```

**Test Principles**:
- ✅ Real MongoDB operations (NO mocks)
- ✅ Full CRUD cycle: Create → Read → Update → Delete → Verify
- ✅ Database state verification after every operation
- ✅ Cleanup after each test (fixtures with teardown)
- ✅ Follow existing test_wallet_crud.py pattern

---

#### Phase 2: Frontend Integration (Days 4-5)

**Goal**: Wire up existing components into app routing and navigation

**Step 1: Add Routes to App.tsx**
- [ ] Add lazy imports for 4 pages (LeaderboardPage, DiscoverPage, ActivityFeedPage, UserProfilePage)
- [ ] Add protected routes for `/leaderboard`, `/discover`, `/feed`, `/user/:userId`

**Step 2: Update Navigation**
- [ ] **Header.tsx**: Add Leaderboard and Discover links with icons (TrendingUp, Compass)
- [ ] **MobileBottomNav.tsx**: Update nav items (Leaders, Discover icons)

**Step 3: Create Missing Pages (3 files)**
- [ ] **LeaderboardPage.tsx** (~200 lines)
  - Reuse existing Leaderboard component (show 50-100 entries)
  - User rank card at top
  - Period selector (Week/Month/All Time)
  - Auto-scroll to user position
  - Responsive layout (mobile: 1-col, desktop: 2-col)

- [ ] **DiscoverPage.tsx** (~250 lines)
  - Search bar with 300ms debouncing
  - Follow suggestions section
  - Popular users grid (2-col mobile, 3-col tablet, 4-col desktop)
  - Reuse UserCard + FollowButton components

- [ ] **ActivityFeedPage.tsx** (~180 lines)
  - Filter tabs (All/Started/Completed/Milestones)
  - Reuse ActivityCard component
  - Pull-to-refresh on mobile
  - Auto-refetch every 2 minutes

**Step 4: Complete UserProfilePage Tabs**
- [ ] **Completed Books Tab** (~30 lines)
  - Filter activities for completed_book type
  - Display as grid with checkmark badges
  - Empty state: "No completed books yet"

- [ ] **Reviews Tab** (~20 lines)
  - MVP: Keep placeholder with improved message
  - Future: Implement after backend reviews API (see Book Clubs feature below)

---

#### Phase 3: Frontend Component Tests (Day 6)

**Goal**: Test coverage for critical social components

**Setup**:
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom
```

**Test Files to Create** (4 files):
- [ ] **ActivityCard.test.tsx**
  - [ ] Renders started_book activity
  - [ ] Renders completed_book activity
  - [ ] Renders milestone activity
  - [ ] Shows/hides user info based on showUser prop
  - [ ] Time formatting (date-fns)

- [ ] **FollowButton.test.tsx**
  - [ ] Renders "Follow" when not following
  - [ ] Renders "Following" when following
  - [ ] Hover shows "Unfollow"
  - [ ] Click triggers follow mutation
  - [ ] Loading state disables button
  - [ ] Redirects to login if not authenticated

- [ ] **Leaderboard.test.tsx**
  - [ ] Renders top 10 users
  - [ ] Medal icons for top 3
  - [ ] Period selector works
  - [ ] Anonymous users handled
  - [ ] Loading skeleton
  - [ ] Empty state

- [ ] **useSocial.test.ts**
  - [ ] useFollowUser mutation
  - [ ] useUnfollowUser mutation
  - [ ] Query invalidation on success
  - [ ] Toast notifications
  - [ ] Error handling

---

#### Phase 4: API Integration Testing (Day 7)

**Goal**: Test actual API endpoints with real data flow

**Test File**: test_api_integration.py
- [ ] Create test user via API (POST /auth/signup)
- [ ] Follow another user (POST /social/follow/{userId})
- [ ] Verify follow in database (MongoDB query)
- [ ] Get followers list (GET /social/followers/{userId})
- [ ] Create reading activity (POST /activity/started)
- [ ] Get activity feed (GET /social/feed)
- [ ] Unfollow user (DELETE /social/follow/{userId})
- [ ] Verify unfollow in database
- [ ] Delete test data (cleanup)

**Tools**: httpx.AsyncClient, real MongoDB, real auth tokens

---

#### Phase 5: Mobile Testing & Optimization (Days 8-9)

**Goal**: Verify responsive design on real devices

**Devices to Test**:
- [ ] iPhone (Safari iOS 14+)
- [ ] Android (Chrome 90+)
- [ ] iPad/Tablet
- [ ] Desktop browsers (Chrome, Firefox, Safari)

**Test Scenarios** (per device):
1. **Navigation**
   - [ ] Bottom nav works (tap all 5 items)
   - [ ] Links navigate correctly
   - [ ] Back button behavior

2. **Leaderboard**
   - [ ] Period selector taps work
   - [ ] List scrolls smoothly
   - [ ] User rank card visible
   - [ ] Medal icons render

3. **Discover**
   - [ ] Search input focus + keyboard
   - [ ] Debouncing works (no lag)
   - [ ] User cards tap-friendly (44×44px targets)
   - [ ] Follow button state updates
   - [ ] Grid responsive (2-col mobile)

4. **Activity Feed**
   - [ ] Pull-to-refresh gesture
   - [ ] Activity cards readable
   - [ ] Book covers load
   - [ ] Infinite scroll (if implemented)

5. **User Profile**
   - [ ] Avatar loads
   - [ ] Stats display correctly
   - [ ] Tab switching works
   - [ ] Currently Reading grid (2-col mobile)
   - [ ] Follow button accessible
   - [ ] Share button works (native share API)

**Performance Checks**:
- [ ] Page load < 3s on 3G
- [ ] No memory leaks (DevTools)
- [ ] 60fps scrolling
- [ ] Images lazy load
- [ ] No console errors

**Accessibility Checks**:
- [ ] Touch targets ≥ 44×44px
- [ ] Contrast ratios WCAG AA
- [ ] Keyboard navigation
- [ ] Screen reader labels

**Common Fixes** (if needed):
- [ ] Touch targets too small → increase padding to px-4 py-3
- [ ] Images not lazy → add `loading="lazy"`
- [ ] Slow API calls → add React Query caching
- [ ] Jank scrolling → use `will-change: transform`
- [ ] Keyboard issues → ensure `inputMode` correct

---

#### Success Criteria (MVP) ✅

Must Have:
- [ ] All 9 backend test files pass (120+ tests)
- [ ] All 3 frontend pages render and function
- [ ] Routes and navigation work
- [ ] Follow/unfollow works end-to-end
- [ ] Leaderboard shows real data
- [ ] Discover search works
- [ ] Activity feed shows followed users' activities
- [ ] Mobile responsive (tested on 2+ devices)
- [ ] Zero console errors
- [ ] Test coverage ≥ 75%

Nice to Have (Phase 2):
- [ ] Notification system UI
- [ ] User blocking/reporting UI
- [ ] Reviews feature (backend + frontend)
- [ ] Real-time updates (WebSocket)
- [ ] Advanced filters on feed
- [ ] Leaderboard achievements/badges

---

#### 📚 NEW FEATURE: Book Clubs (Discovered During Planning)

**User Story**: "As a user, I want to be able to create a book club, invite friends to join or make it open, and have a live comment section in the book club."

**Feature Requirements**:
1. Create book club (name, description, book, privacy: private/open)
2. Invite friends to join (private clubs) OR make discoverable (open clubs)
3. Live comment section for club members
4. Real-time updates (WebSocket or polling)
5. Club member management (owner, members, roles)

**Implementation Plan** (Future Phase):

**Backend** (New Models & Services):
- [ ] **BookClub Model** (backend/app/models/book_club.py)
  - club_id, name, description, book_id, owner_id
  - privacy: "private" | "open"
  - member_ids[], created_at, updated_at
  - member_limit (optional)

- [ ] **ClubComment Model** (backend/app/models/book_club.py)
  - comment_id, club_id, user_id, message, chapter_reference
  - reply_to_id (for threading), created_at, edited_at
  - reactions: {emoji: [user_ids]}

- [ ] **ClubInvitation Model** (backend/app/models/book_club.py)
  - invitation_id, club_id, inviter_id, invitee_id/email
  - status: "pending" | "accepted" | "rejected"
  - token (for email invites), expires_at

**Backend API Routes**:
- [ ] POST /api/v1/book-clubs - Create club
- [ ] GET /api/v1/book-clubs - List user's clubs
- [ ] GET /api/v1/book-clubs/{club_id} - Get club details
- [ ] PUT /api/v1/book-clubs/{club_id} - Update club
- [ ] DELETE /api/v1/book-clubs/{club_id} - Delete club
- [ ] POST /api/v1/book-clubs/{club_id}/members - Add member
- [ ] DELETE /api/v1/book-clubs/{club_id}/members/{user_id} - Remove member
- [ ] POST /api/v1/book-clubs/{club_id}/invite - Send invitation
- [ ] GET /api/v1/book-clubs/discover - Discover open clubs
- [ ] POST /api/v1/book-clubs/{club_id}/comments - Post comment
- [ ] GET /api/v1/book-clubs/{club_id}/comments - Get comments (with pagination)
- [ ] PUT /api/v1/book-clubs/{club_id}/comments/{comment_id} - Edit comment
- [ ] DELETE /api/v1/book-clubs/{club_id}/comments/{comment_id} - Delete comment
- [ ] POST /api/v1/book-clubs/{club_id}/comments/{comment_id}/react - Add reaction

**Frontend Components**:
- [ ] BookClubListPage - Show user's clubs
- [ ] BookClubDetailPage - Club info + comment section
- [ ] CreateBookClubModal - Create club form
- [ ] InviteMembersModal - Invite friends
- [ ] ClubCommentSection - Live comments with WebSocket
- [ ] ClubMembersList - Show members with roles

**WebSocket Integration**:
- [ ] Real-time comment updates (new comments appear instantly)
- [ ] Typing indicators ("Alice is typing...")
- [ ] Online member presence
- [ ] Read receipts (optional)

**Integration Points**:
- Leverages existing social features (follow system for suggestions)
- Uses existing book data
- Uses existing user profiles and avatars
- Can integrate with reading progress (comment at specific chapter/chunk)

**Testing Requirements**:
- [ ] Backend unit tests (club CRUD, comments, invitations)
- [ ] WebSocket tests (real-time updates)
- [ ] Frontend component tests
- [ ] E2E tests (create club → invite → comment → receive update)

**Timeline Estimate**: 5-7 days (after social features complete)

---

#### Implementation Order & Dependencies

```
Day 1-2: Backend Tests (Follow, Blocking, Reporting) ← IN PROGRESS
Day 2-3: Backend Tests (Activity, Leaderboard, Discovery, Stats)
         ↓
Day 4:   Frontend Integration (Routes, Nav, LeaderboardPage)
Day 5:   Frontend Pages (DiscoverPage, ActivityFeedPage, Profile tabs)
         ↓
Day 6:   Frontend Component Tests
Day 7:   API Integration Tests
         ↓
Day 8-9: Mobile Testing & Fixes
```

**Parallel Work Possible**:
- Days 1-3: Backend tests (one person)
- Days 4-5: Frontend integration (another person simultaneously)
- Days 6-7: Tests can overlap with final bug fixes

---

#### Critical Files Summary

**Backend Tests** (NEW - 9 files):
1. `/opt/kasaai/apps/inkwave/backend/tests/test_social_follow_unfollow.py` ✅ COMPLETE
2. `/opt/kasaai/apps/inkwave/backend/tests/test_social_blocking.py`
3. `/opt/kasaai/apps/inkwave/backend/tests/test_social_reporting.py`
4. `/opt/kasaai/apps/inkwave/backend/tests/test_reading_activity_crud.py`
5. `/opt/kasaai/apps/inkwave/backend/tests/test_activity_feed.py`
6. `/opt/kasaai/apps/inkwave/backend/tests/test_leaderboard.py`
7. `/opt/kasaai/apps/inkwave/backend/tests/test_user_discovery.py`
8. `/opt/kasaai/apps/inkwave/backend/tests/test_username_management.py`
9. `/opt/kasaai/apps/inkwave/backend/tests/test_social_stats_denormalization.py`

**Frontend Pages** (NEW - 3 files):
10. `/opt/kasaai/apps/inkwave/frontend/src/pages/LeaderboardPage.tsx`
11. `/opt/kasaai/apps/inkwave/frontend/src/pages/DiscoverPage.tsx`
12. `/opt/kasaai/apps/inkwave/frontend/src/pages/ActivityFeedPage.tsx`

**Frontend Tests** (NEW - 4 files):
13. `/opt/kasaai/apps/inkwave/frontend/src/components/ActivityCard.test.tsx`
14. `/opt/kasaai/apps/inkwave/frontend/src/components/FollowButton.test.tsx`
15. `/opt/kasaai/apps/inkwave/frontend/src/components/Leaderboard.test.tsx`
16. `/opt/kasaai/apps/inkwave/frontend/src/hooks/useSocial.test.ts`

**Frontend Integration** (MODIFY - 4 files):
17. `/opt/kasaai/apps/inkwave/frontend/src/App.tsx` - Add 4 routes
18. `/opt/kasaai/apps/inkwave/frontend/src/components/Header.tsx` - Add 2 nav links
19. `/opt/kasaai/apps/inkwave/frontend/src/components/MobileBottomNav.tsx` - Update nav items
20. `/opt/kasaai/apps/inkwave/frontend/src/pages/UserProfilePage.tsx` - Complete 2 tabs

**Total**: 16 new files + 4 modifications = 20 files

---

## 🎉 Previous Update: Admin User Analytics Dashboard (2025-12-01)

### ✅ ADMIN USER ANALYTICS COMPLETE

**Implementation Summary**: Created comprehensive admin analytics dashboard showing user signups, login statistics, user activity patterns, and detailed book playback progress for each user.

#### Backend Implementation ✅ COMPLETE
- [x] **User Statistics Endpoint** (backend/app/api/routes/admin.py)
  - GET `/api/v1/admin/analytics/user-stats` - Get overall user statistics
  - Returns: total_signed_up, total_logged_in, active_users_30d, active_users_7d
  - Queries MongoDB users collection with date filters

- [x] **User Activity Analytics Endpoint** (backend/app/api/routes/admin.py)
  - GET `/api/v1/admin/analytics/user-activity` - Get where users spend most time
  - Returns: total_reading_time_minutes, total_interactions, unique_books_accessed, total_sessions, average_session_duration_minutes, primary_activity
  - Aggregates data from reading_sessions and interactions collections

- [x] **User Book Progress Endpoint** (backend/app/api/routes/admin.py)
  - GET `/api/v1/admin/analytics/user-book-progress` - Get per-user book playback statistics
  - Returns: List of user-book progress records with:
    - User information (email, display name)
    - Book information (title, author)
    - Progress percentage and chunk position
    - Time spent per book
    - Completion status
    - Last accessed timestamp
  - Supports optional user_id filter and limit parameter

- [x] **Enhanced User Analytics Endpoint** (backend/app/api/routes/admin.py)
  - GET `/api/v1/admin/analytics/users` - Enhanced with real MongoDB queries
  - Returns per-user analytics: listening time, unique books count, sessions count, wallet balance
  - Supports sorting by usage, signup_date, or revenue
  - Replaced mock data with real database queries

#### Frontend Implementation ✅ COMPLETE
- [x] **Admin User Analytics Page** (frontend/src/pages/AdminUserAnalyticsPage.tsx)
  - Three-tab interface: Overview, Users, Book Progress
  - Overview tab shows:
    - Total signed up users card
    - Total logged in users card
    - Active users (30d/7d) card
    - Total reading time card
    - User activity section showing where users spend time
  - Users tab shows:
    - Searchable table of all users
    - Sortable by usage, signup date, or revenue
    - Displays: email, signup date, last active, listening time, books count, sessions, wallet balance
  - Book Progress tab shows:
    - Searchable table of user-book progress
    - Displays: user info, book info, progress bar with percentage, time spent, completion status, last accessed
    - Visual progress bars for each book

- [x] **API Client Updates** (frontend/src/lib/api.ts)
  - Added `admin.getUserStats()` method
  - Added `admin.getUserActivity()` method
  - Added `admin.getUserBookProgress()` method

- [x] **Routing Updates** (frontend/src/App.tsx)
  - Added route `/admin/analytics/users` for new analytics page
  - Lazy-loaded component for performance

- [x] **Admin Dashboard Link** (frontend/src/pages/AdminDashboardPage.tsx)
  - Added "User Analytics" section card linking to new analytics page

#### Features
- **User Statistics**: Real-time counts of signed up, logged in, and active users
- **Activity Tracking**: Shows where users spend most time (reading vs Q&A)
- **Book Progress**: Detailed view of how much each user has played of each book
- **Search & Filter**: Search users and books, sort by multiple criteria
- **Visual Progress**: Progress bars showing book completion percentage
- **Responsive Design**: Mobile-friendly tables and cards

#### API Examples
```bash
# Get user statistics
GET /api/v1/admin/analytics/user-stats

# Response
{
  "total_signed_up": 150,
  "total_logged_in": 120,
  "active_users_30d": 45,
  "active_users_7d": 12
}

# Get user activity
GET /api/v1/admin/analytics/user-activity

# Response
{
  "total_reading_time_minutes": 1250,
  "total_interactions": 340,
  "unique_books_accessed": 25,
  "total_sessions": 180,
  "average_session_duration_minutes": 6.94,
  "primary_activity": "Reading audiobooks"
}

# Get user book progress
GET /api/v1/admin/analytics/user-book-progress?limit=100

# Response
{
  "progress_records": [
    {
      "user_id": "user_123",
      "user_email": "user@example.com",
      "book_title": "The Art of Winning",
      "progress_percentage": 45.5,
      "time_spent_minutes": 120,
      "is_completed": false
    }
  ],
  "total_count": 85
}
```

#### Deployment Status ✅ READY
- [x] Backend endpoints implemented and tested
- [x] Frontend page created with full functionality
- [x] API client methods added
- [x] Routing configured
- [x] Admin dashboard link added
- [ ] Unit tests pending (future work)

---

## 🎉 Previous Update: Slack Webhook for New Signups (2025-11-30)

### ✅ SLACK NOTIFICATION INTEGRATION COMPLETE

**Implementation Summary**: Integrated Slack webhook notifications to alert the team whenever a new user signs up for InkWave. Notifications include user email, signup source (direct or via invitation), and book details if applicable.

#### Backend Implementation ✅ COMPLETE
- [x] **Slack Webhook Configuration** (backend/app/core/config.py)
  - Added `SLACK_WEBHOOK_URL` setting
  - Configurable via environment variable or default

- [x] **Slack Notification Service** (backend/app/services/slack_notification_service.py)
  - `send_message()` - Send raw Slack message with blocks
  - `notify_new_signup()` - Formatted notification for new signups
  - Rich message blocks with headers, fields, and dividers
  - Email, user ID (truncated), timestamp, signup source
  - Book info for invitation-based signups
  - Async HTTP client (httpx) with timeout handling
  - Graceful error handling (doesn't fail signup on notification failure)

- [x] **Signup Integration** (backend/app/api/routes/auth.py)
  - Added Slack notification call after successful signup
  - Passes user email, ID, invitation status, and book title
  - Wrapped in try/except to prevent signup failures

- [x] **Dependencies** (backend/requirements.txt)
  - Added httpx>=0.26,<0.29 (compatible with Supabase)

#### Notification Format
```
Header: "New InkWave Signup"
Fields:
  - Email: user@example.com
  - User ID: abc123...
  - Timestamp: 2025-11-30 09:26:33 UTC
  - Source: Direct Signup | Invitation Link
  - Book Added: [if from invitation]
```

#### Deployment Status ✅ DEPLOYED
- [x] Backend service restarted successfully
- [x] Slack webhook tested and working
- [x] Notifications appearing in Slack channel

---

## 🎉 Previous Update: Book Invitation Links for User Access (2025-11-30)

### ✅ BOOK INVITATION FEATURE COMPLETE

**Implementation Summary**: Created a book invitation/access link system that allows admins to generate shareable URLs. When users register via these links, they automatically get access to the specified audiobook in their library.

#### Backend Implementation ✅ COMPLETE
- [x] **BookInvitation Model** (backend/app/models/book_invitation.py)
  - Secure token generation with `secrets.token_urlsafe`
  - Max uses limit (optional)
  - Expiration date (optional)
  - Welcome message (optional)
  - Usage tracking (redeemed_by list)
  - Status methods (active, expired, exhausted, revoked)

- [x] **User Model Enhancement** (backend/app/models/user.py)
  - Added `LibraryBook` model for user's book access
  - Added `library_books` field to User model
  - Tracks access_type, invitation_id, granted_by

- [x] **BookInvitationService** (backend/app/services/book_invitation_service.py)
  - `create_invitation()` - Create invitation with book details
  - `get_invitation()` - Get invitation by token
  - `list_invitations()` - List all invitations (with filters)
  - `revoke_invitation()` - Revoke an invitation
  - `redeem_invitation()` - Redeem invitation for user
  - `get_user_library()` - Get user's library books
  - `check_user_has_book_access()` - Check access
  - `get_invitation_stats()` - Admin statistics

- [x] **Book Invitation API Routes** (backend/app/api/routes/book_invitations.py)
  - POST `/api/v1/book-invitations` - Create invitation (Admin)
  - GET `/api/v1/book-invitations` - List invitations (Admin)
  - DELETE `/api/v1/book-invitations/{id}` - Revoke invitation (Admin)
  - GET `/api/v1/book-invitations/stats` - Get statistics (Admin)
  - GET `/api/v1/book-invitations/public/{id}` - Get public info (Public)
  - POST `/api/v1/book-invitations/{id}/redeem` - Redeem invitation (Auth)
  - GET `/api/v1/book-invitations/my-library` - Get user's library (Auth)

- [x] **Signup Enhancement** (backend/app/api/routes/auth.py)
  - Added `invitation_token` parameter to signup
  - Automatic redemption on signup
  - Returns invitation status and book info

#### Frontend Implementation ✅ COMPLETE
- [x] **API Client Methods** (frontend/src/lib/api.ts)
  - `api.bookInvitations.create()` - Create invitation
  - `api.bookInvitations.list()` - List invitations
  - `api.bookInvitations.revoke()` - Revoke invitation
  - `api.bookInvitations.getStats()` - Get statistics
  - `api.bookInvitations.getPublicInfo()` - Get public info
  - `api.bookInvitations.redeem()` - Redeem invitation
  - `api.bookInvitations.getMyLibrary()` - Get library

- [x] **Auth Store Enhancement** (frontend/src/store/authStore.ts)
  - Updated `signUp()` to accept invitation token
  - Returns invitation redemption status
  - Returns library book info

- [x] **Signup Page Enhancement** (frontend/src/pages/SignupPage.tsx)
  - Reads `?invite=<token>` from URL
  - Fetches and displays invitation info
  - Shows book cover, title, author, welcome message
  - Passes token to signup
  - Redirects to book page after signup

- [x] **BookInvitationModal** (frontend/src/components/BookInvitationModal.tsx)
  - Generate invitation links with options:
    - Maximum uses limit
    - Expiration in days
    - Custom welcome message
  - Copy link to clipboard
  - View existing invitations
  - Revoke invitations
  - Status badges (active, expired, exhausted, revoked)

- [x] **MyBooksPage Integration** (frontend/src/pages/MyBooksPage.tsx)
  - Added "Share Access" option to book dropdown menu
  - Opens BookInvitationModal for selected book
  - Green Share2 icon for visual distinction

#### Usage Flow
1. **Admin creates invitation**:
   - Navigate to My Books page
   - Click book menu → "Share Access"
   - Configure options (optional: max uses, expiry, message)
   - Click "Generate Invitation Link"
   - Copy the generated URL

2. **User registers via link**:
   - Opens link like `https://inkwave.ailabsafrica.com/signup?invite=<token>`
   - Sees book info on signup page
   - Fills in registration form
   - On signup, book is automatically added to library
   - Redirected to book page

#### API Examples
```bash
# Create invitation (Admin)
POST /api/v1/book-invitations
{
  "book_id": "book_abc123",
  "max_uses": 10,
  "expires_in_days": 30,
  "welcome_message": "Enjoy this audiobook!"
}

# Response
{
  "invitation_id": "X2k9...",
  "invitation_url": "https://inkwave.ailabsafrica.com/signup?invite=X2k9...",
  "book_title": "The Art of Winning",
  "status": "active"
}

# Get public info (for signup page)
GET /api/v1/book-invitations/public/X2k9...

# Response
{
  "valid": true,
  "book_title": "The Art of Winning",
  "book_cover_url": "/static/covers/...",
  "book_author": "John Smith",
  "welcome_message": "Enjoy this audiobook!",
  "status": "active"
}
```

#### Deployment Status ✅ DEPLOYED
- [x] Backend service restarted successfully
- [x] Frontend built successfully
- [x] All endpoints functional
- [x] API documentation available at /api/docs

---

## 🎉 Previous Update: Reference Audio Upload for Zero-Shot TTS (2025-11-29)

### ✅ BACKEND API FOR REFERENCE AUDIO UPLOAD COMPLETE

**Implementation Summary**: Created backend API endpoints for uploading reference audio files that can be used with zero-shot TTS clone providers (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS) for audiobook narration.

#### Backend Implementation ✅ COMPLETE
- [x] **Reference Audio API Routes** (backend/app/api/routes/reference_audio.py)
  - POST `/api/v1/reference-audio/upload` - Upload reference audio file
  - GET `/api/v1/reference-audio/` - List all reference audio for user
  - GET `/api/v1/reference-audio/{id}` - Get reference audio metadata
  - GET `/api/v1/reference-audio/{id}/audio` - Serve audio file
  - DELETE `/api/v1/reference-audio/{id}` - Delete reference audio
  - File validation (format, size up to 10MB)
  - Audio duration detection using librosa
  - Optional voice library entry creation
  - MongoDB storage for metadata

- [x] **Storage Integration**
  - Local file storage in `/opt/kasaai/apps/inkwave/backend/storage/reference_audio/`
  - File serving endpoint for audio playback
  - Support for WAV, MP3, OGG, FLAC, M4A formats

- [x] **Voice Library Integration**
  - Optional automatic voice library entry creation
  - Links reference audio to voice library for easy selection
  - Supports metadata (gender, language, tags)

- [x] **Router Registration** (backend/app/main.py)
  - Reference audio router registered at `/api/v1/reference-audio`

#### Features
- **Zero-Shot TTS Support**: Compatible with StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS
- **File Validation**: Size limits (10MB), format validation, content type checking
- **Audio Analysis**: Automatic duration detection
- **Optional Voice Creation**: Can create voice library entry during upload
- **User-Scoped**: All reference audio is scoped to user and organization

#### API Examples
```bash
# Upload reference audio
POST /api/v1/reference-audio/upload
Content-Type: multipart/form-data
- audio_file: <audio file>
- name: "My Voice"
- description: "Narration voice"
- create_voice: true
- gender: "male"
- language: "en"

# Response
{
  "success": true,
  "reference_audio_id": "ref_audio_abc123",
  "voice_id": "voice_xyz789",
  "audio_url": "/storage/reference_audio/user123/ref_audio_abc123.wav",
  "file_size_bytes": 245678,
  "duration_seconds": 8.5,
  "compatible_providers": ["styletts2", "coqui_xtts", "openvoice", "f5tts"]
}
```

#### Frontend Implementation ✅ COMPLETE
- [x] **Reference Audio Upload Component** (frontend/src/components/reference-audio/ReferenceAudioUpload.tsx)
  - Drag-and-drop file upload interface
  - Audio preview with play/pause controls
  - File validation (format, size)
  - Metadata form (name, description, tags)
  - Optional voice library entry creation
  - Upload progress indicators
  - Elegant UI matching inkwave dark theme

- [x] **Reference Audio List Component** (frontend/src/components/reference-audio/ReferenceAudioList.tsx)
  - Grid display of reference audio files
  - Audio playback controls
  - Delete functionality with confirmation
  - Upload modal integration
  - Compatible providers display
  - File metadata (duration, size)
  - Empty state with upload prompt

- [x] **Voice Settings Integration** (frontend/src/pages/VoiceSettingsPage.tsx)
  - New "Reference Audio" tab added
  - Integrated ReferenceAudioList component
  - Easy access to upload and manage reference audio

- [x] **API Client Methods** (frontend/src/lib/api.ts)
  - `api.referenceAudio.upload()` - Upload with FormData
  - `api.referenceAudio.list()` - List all reference audio
  - `api.referenceAudio.get()` - Get metadata
  - `api.referenceAudio.getAudio()` - Get audio blob
  - `api.referenceAudio.delete()` - Delete reference audio

#### TTS Service Integration ✅ COMPLETE
- [x] **Reference Audio Support** (backend/app/services/tts_service.py)
  - New method: `_narrate_with_reference_audio()`
  - Detects `voice_id` starting with `ref_audio_` prefix
  - Loads reference audio from database/storage
  - Converts to base64 for TTS provider
  - Calls zero-shot TTS provider (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS)
  - Automatic fallback to default synthesis on error

#### Usage Flow
1. **Upload**: User uploads reference audio via Voice Settings → Reference Audio tab
2. **Select**: Reference audio can be used as `voice_id` (e.g., `ref_audio_abc123`)
3. **Synthesize**: TTS service automatically detects and uses reference audio for zero-shot TTS
4. **Narrate**: Audiobook narration uses the cloned voice from reference audio

#### Pending Work
- [ ] Unit tests for reference audio upload and usage
- [ ] Integration tests for TTS synthesis with reference audio
- [ ] Frontend: Show reference audio options in voice selector for zero-shot providers

---

## 🎉 Previous Update: TTS Component & Import Path Fixes (2025-11-28)

### ✅ TTS AND STORAGE COMPONENT FIXES COMPLETE

**Implementation Summary**: Fixed multiple import path issues in shared library usage and corrected TTS hook usage in frontend components.

#### Backend Import Path Fixes ✅ COMPLETE
- [x] **storage.py** (backend/app/api/routes/storage.py)
  - Fixed sys.path import to use project root `/opt/kasaai/`
  - Changed from hardcoded path to dynamic Path calculation
  - Now correctly imports from `apps.shared.routes.storage_routes`

- [x] **storage_service.py** (backend/app/services/storage_service.py)
  - Fixed sys.path import to use project root `/opt/kasaai/`
  - Changed from `from shared.storage...` to `from apps.shared.storage...`
  - Consistent with other InkWave imports

- [x] **tts_service.py** (backend/app/services/tts_service.py)
  - Standardized import path calculation using `pathlib.Path`
  - Now consistent with main.py path setup

- [x] **tts.py routes** (backend/app/api/routes/tts.py)
  - Fixed import path from `/opt/kasaai/apps` to `/opt/kasaai/`
  - Corrected imports from `apps.shared.integration.ai_services...`

#### Frontend Component Fixes ✅ COMPLETE
- [x] **BookVoiceSettingsModal.tsx** (frontend/src/components/BookVoiceSettingsModal.tsx)
  - Fixed `useComprehensiveTTS()` hook call without required `apiBaseUrl` parameter
  - Added local state management for `selectedProvider`, `selectedVoice`, `speed`, `pitch`
  - Now correctly passes `API_BASE_URL` and `endpointPath` to the hook
  - Prevents relative URL requests that hit frontend nginx instead of API

- [x] **Manifest permissions** (frontend/dist/)
  - Fixed 403 errors for `manifest.webmanifest` and `sw.js`
  - Changed permissions from `rw-------` to `rw-r--r--`

#### Issues Fixed
1. **Import Path Inconsistency**: Some files used `/opt/kasaai/apps` with `apps.shared...` imports (incorrect - results in `/opt/kasaai/apps/apps/shared/`)
2. **TTS Provider Errors**: Frontend `useComprehensiveTTS` hook was called without required parameters, causing relative URL requests to frontend instead of API
3. **PWA 403 Errors**: manifest.webmanifest and sw.js had owner-read-only permissions

#### Technical Details
- Path calculation standardized: `project_root = Path(__file__).parent.parent...parent`
- All imports now use `from apps.shared...` with path `/opt/kasaai/`
- Frontend hook now properly receives `API_BASE_URL` and `endpointPath`
- Service restarted and frontend rebuilt

#### Deployment Status ✅ DEPLOYED
- [x] Backend service restarted: `sudo systemctl restart kasaai-inkwave-backend`
- [x] All startup checks passed:
  - ✅ MongoDB connected
  - ✅ Organization service initialized
  - ✅ Default providers initialized
  - ✅ Wallet service initialized
  - ✅ Storage file serving routes initialized
- [x] Frontend rebuilt: `npm run build` completed successfully
- [x] Manifest/SW permissions fixed

---

## 🎉 Previous Update: Dynamic Author Image Search (2025-11-28)

### ✅ AUTHOR IMAGE SEARCH FEATURE COMPLETE

**Implementation Summary**: Added dynamic author image search functionality that automatically fetches author photos from the web during book upload. Images are stored as external URLs (not locally) for dynamic display.

#### Backend Implementation ✅ COMPLETE
- [x] **AuthorImageSearchService** (backend/app/services/author_image_service.py)
  - Brave Search API integration for image search
  - Tavily API fallback
  - Multi-query search strategy (author photo, Amazon author, Wikipedia)
  - URL validation and quality ranking
  - Result deduplication and scoring
  - Async HTTP requests with timeout handling

- [x] **Author Image API Routes** (backend/app/api/routes/author_images.py)
  - GET /api/v1/author-images/search - Search for author images
  - POST /api/v1/author-images/search - Search via POST body
  - POST /api/v1/author-images/lookup-for-book/{book_id} - Update existing book
  - POST /api/v1/author-images/bulk-update - Bulk update books without images

- [x] **Book Model Enhancement** (backend/app/models/book.py)
  - Added `author_image_url` field (dynamic URL, not stored locally)

- [x] **Book Upload Integration** (backend/app/api/routes/books.py)
  - Auto-search for author image during book upload
  - Optional `author_image_url` parameter
  - `auto_search_author_image` flag (default: True)
  - Graceful fallback if search fails

- [x] **Book Service Updates** (backend/app/services/book_service.py)
  - All book queries now return `author_image_url`
  - list_books, get_book, search_books, get_continue_reading
  - list_books_by_uploader

#### Frontend Implementation ✅ COMPLETE
- [x] **BookDetailPage Enhancement** (frontend/src/pages/BookDetailPage.tsx)
  - Display author image next to author name
  - Circular image with purple border
  - Error handling for broken images (graceful hide)

- [x] **API Client Update** (frontend/src/lib/api.ts)
  - authorImages.search() - Search by author name
  - authorImages.searchPost() - Search via POST
  - authorImages.lookupForBook() - Update existing book
  - authorImages.bulkUpdate() - Bulk update books

#### Unit Tests ✅ COMPLETE
- [x] **Test Suite** (backend/tests/test_author_image_search.py)
  - 15+ test cases
  - Test search with valid/invalid names
  - Test popular authors (Stephen King)
  - Test empty/whitespace input
  - Test URL validation
  - Test deduplication and ranking
  - Test API endpoints (GET/POST)
  - Test parameter validation

#### Configuration ✅ COMPLETE
- [x] **Environment Variables** (backend/.env)
  - BRAVE_API_KEY for image search
  - TAVILY_API_KEY as fallback

#### Deployment ✅ COMPLETE
- [x] Backend service restarted with new endpoints
- [x] Frontend built successfully
- [x] API tested with real authors
  - Nicholas Duncan-Williams: ✅ Found 3 images
  - Stephen King: ✅ Found images

#### Key Features
- **Dynamic Images**: External URLs stored, not local files
- **Auto-Search**: Automatically finds author photos during upload
- **Multiple Sources**: Brave Search + Tavily fallback
- **Quality Ranking**: Prefers Amazon/Wikipedia sources
- **Graceful Degradation**: Won't fail upload if search fails

#### API Examples
```bash
# Search for author images
GET /api/v1/author-images/search?author_name=Nicholas%20Duncan-Williams&context=bishop&max_results=3

# Response
{
  "query": "Nicholas Duncan-Williams",
  "image_urls": ["https://cdn.modernghana.com/...jpg", ...],
  "primary_image_url": "https://cdn.modernghana.com/...jpg",
  "status": "success"
}
```

---

## 🎉 Previous Update: Enhanced Book Creation Flow with Cover Image Upload (2025-11-13)

### ✅ BOOK CREATION FLOW ENHANCEMENT COMPLETE

**Implementation Summary**: Enhanced the book creation flow on InkWave with complete cover image upload functionality. Admins/authors can now upload PDF books along with cover images (or URLs), which are automatically processed into the vector database and immediately available on the interface for narration with proper visual representation.

#### Book Upload & Processing ✅ COMPLETE
- [x] **Enhanced Backend Book Upload API** (backend/app/api/routes/books.py:273-399)
  - POST /api/v1/books/upload - Enhanced endpoint with cover image support
  - PDF file validation (max 100MB)
  - **NEW:** Cover image file upload (JPG, PNG, WebP, max 5MB)
  - **NEW:** Cover image validation and storage in /static/covers/
  - **NEW:** Unique filename generation with UUID
  - Cover URL fallback option for web-hosted images
  - Automatic cleanup on errors
  - Form data handling for all book metadata
  - Integrated with BookProcessingService

- [x] **Enhanced Admin Book Upload API** (backend/app/api/routes/admin.py:284-421)
  - POST /api/v1/admin/books/upload - Admin endpoint with cover upload
  - **NEW:** Cover image file upload support
  - **NEW:** Image format and size validation
  - **NEW:** Automatic file storage and URL generation
  - Comprehensive error handling with cleanup
  - Logging for debugging and monitoring

- [x] **Book Processing Service** (backend/app/services/book_processing_service.py)
  - PDF text extraction using shared DocumentProcessor
  - Automatic chapter detection (Chapter 1, Part 1, Section 1 patterns)
  - Smart chunking (1000 chars, 200 overlap)
  - Embedding generation via RAG service
  - MongoDB storage for books and chunks
  - Processing status tracking (pending → processing → ready/error)
  - Comprehensive error handling and logging

- [x] **Static File Infrastructure** (backend/app/main.py & backend/static/)
  - **NEW:** /static/covers/ directory for book cover images
  - Mounted static file serving on FastAPI
  - Unique filename generation with UUID
  - Automatic cleanup on errors
  - Public URL format: /static/covers/{filename}

- [x] **Vector Database Integration** (backend/app/services/book_processing_service.py:150-158)
  - RAG service integration for embeddings
  - Automatic vector generation for book chunks
  - pgvector storage for semantic search
  - Book Q&A capability enabled

#### Admin Panel Enhancements ✅ COMPLETE
- [x] **Admin Dashboard Updates** (frontend/src/pages/AdminDashboardPage.tsx)
  - "Book Creation" as primary admin section
  - Renamed from "Upload Books" to emphasize creation workflow
  - Updated description: "Upload PDF books and cover images for narration"
  - Priority placement in admin sections grid

- [x] **Enhanced Book Upload Page** (frontend/src/pages/BookUploadPage.tsx)
  - Drag-and-drop PDF upload (up to 100MB)
  - **NEW:** Cover image file upload with live preview
  - **NEW:** Visual cover preview (300x400px) with click-to-upload
  - **NEW:** Image format validation (JPG, PNG, WebP)
  - **NEW:** File size validation (max 5MB for cover)
  - **NEW:** Remove cover button for uploaded images
  - Alternative cover URL input (disabled when file uploaded)
  - Real-time form validation
  - Upload progress indicator
  - Recent uploads list with status tracking
  - Form validation for all fields
  - Real-time upload progress
  - Recent uploads display with status tracking
  - File type and size validation
  - Auto-population of title from filename
  - Clear visual feedback and error messages

#### Complete Book Creation Flow
1. **Admin/Author uploads PDF** via /admin/books/upload
   - Select PDF file (drag-and-drop or file picker)
   - Upload cover image (file upload or URL)
   - Fill in metadata (title, author, description)
   - Optional: duration, narrator info

2. **System processes PDF** automatically
   - Extract text from PDF
   - Detect chapters (Chapter 1, Part 1, etc.)
   - Create text chunks (1000 chars, 200 overlap)
   - Generate embeddings for vector database
   - Store in MongoDB (books & book_chunks collections)
   - Save cover image to /static/covers/

3. **Book appears on interface** immediately
   - Visible in book library
   - Cover image displayed
   - Full metadata available
   - Processing status: "ready"

4. **User can listen and generate audio**
   - Click "Listen" button
   - Select TTS provider and voice
   - System narrates book using stored chunks

#### Unit Tests ✅ COMPLETE
- [x] **Book Upload with Cover Tests** (tests/test_book_upload_crud.py)
  - Test upload book with cover image file
  - Test upload book with cover URL
  - Test upload book without cover
  - Test retrieval of books with cover URLs
  - Test listing books includes cover information
  - Test book deletion removes cover files
  - Test cover image validation (formats, sizes)
  - Test complete end-to-end flow
  - 12+ comprehensive test cases
  - Real database integration (no mocks)
  - Automatic cleanup after tests

#### Deployment Status ✅ DEPLOYED
- [x] **Backend Service**
  - Service: kasaai-inkwave-backend.service
  - Status: ✅ Active (running)
  - Port: 30033
  - URL: https://inkwave-api.ailabsafrica.com
  - Static files: https://inkwave-api.ailabsafrica.com/static/
  - Docs: https://inkwave-api.ailabsafrica.com/api/docs

- [x] **Frontend Application**
  - Built successfully (8.13s)
  - Bundle size: 789.51 kB (215.44 kB gzipped)
  - URL: https://inkwave.ailabsafrica.com
  - Admin panel: https://inkwave.ailabsafrica.com/admin

- [x] **Static File Storage**
  - Directory: /opt/kasaai/apps/inkwave/backend/static/covers/
  - Permissions: Configured for read/write
  - Web accessible: ✅

#### Technical Improvements
- **Error Handling**: Comprehensive error handling with automatic cleanup
- **Validation**: File type, size, and format validation for both PDF and images
- **Security**: Unique filename generation prevents overwrites
- **User Experience**: Live preview of cover images before upload
- **Flexibility**: Support for both file upload and URL input
- **Maintainability**: Well-documented code with inline comments
   - Q&A enabled via RAG/vector database

#### Testing & Quality Assurance ✅ COMPLETE
- [x] **Comprehensive Unit Tests** (tests/test_book_upload_crud.py)
  - 12 test cases covering full workflow
  - Test PDF upload with validation
  - Test cover image upload
  - Test book retrieval and listing
  - Test search functionality
  - Test chapter detection
  - Test chunk word counts
  - Test metadata extraction
  - Test error handling (invalid files, missing fields)
  - Test deletion and cleanup
  - All tests use real MongoDB data
  - Proper setup/teardown with test database

#### Key Features
- ✅ PDF upload with drag-and-drop
- ✅ Cover image upload (file or URL)
- ✅ Automatic text extraction
- ✅ Chapter detection
- ✅ Vector database integration
- ✅ Real-time processing status
- ✅ Error handling and validation
- ✅ Static file serving for covers
- ✅ MongoDB storage
- ✅ Recent uploads tracking
- ✅ Comprehensive unit tests

#### API Endpoints
- `POST /api/v1/books/upload` - Upload book with PDF and cover
- `GET /api/v1/books/{book_id}/processing-status` - Check processing status
- `GET /api/v1/books` - List all books
- `GET /api/v1/books/{book_id}` - Get book details
- `POST /api/v1/books/{book_id}/generate-audio` - Generate narration

#### File Structure
```
backend/
├── app/
│   ├── api/routes/books.py           # Upload endpoint
│   ├── services/
│   │   ├── book_processing_service.py # PDF processing
│   │   └── book_service.py            # Book CRUD
│   └── models/book.py                 # Book models
├── static/covers/                     # Cover images
└── tests/test_book_upload_crud.py     # Unit tests

frontend/
├── src/
│   ├── pages/
│   │   ├── AdminDashboardPage.tsx     # Admin panel
│   │   └── BookUploadPage.tsx         # Upload interface
│   └── lib/api.ts                     # API client
```

#### Deployment Status ✅ COMPLETE
- [x] Backend service running
- [x] Frontend built successfully
- [x] Static files directory configured
- [x] MongoDB collections indexed
- [x] RAG service integrated
- [x] All endpoints tested and functional

---

## 🎉 Previous Update: User Profile & Preferences Management (2025-11-12)

### ✅ USER PROFILE AND PREFERENCES COMPLETE

**Implementation Summary**: Full user profile and preferences management system allowing users to personalize their reading experience with voice settings, reading preferences, interaction customization, avatar uploads, and reading statistics.

#### Backend Profile API ✅ COMPLETE
- [x] Enhanced User Profile Service (backend/app/services/user_service.py)
  - CRUD operations for user profiles
  - Profile validation and defaults
  - Integration with existing User model
  - Database indexing (user_id, email, last_active)
  - **NEW:** Avatar file upload with validation (JPG, PNG, WebP, max 5MB)
  - **NEW:** Avatar URL updates
  - **NEW:** User reading statistics aggregation
- [x] Profile Management Endpoints (backend/app/api/routes/profile.py)
  - GET /api/v1/profile - Get current user profile
  - PUT /api/v1/profile - Update user profile
  - PUT /api/v1/profile/voice-preferences - Update voice preferences
  - PUT /api/v1/profile/interaction-preferences - Update interaction preferences
  - PUT /api/v1/profile/reading-level - Update reading level
  - **NEW:** POST /api/v1/profile/avatar/upload - Upload avatar file
  - **NEW:** PUT /api/v1/profile/avatar/url - Set avatar from web URL
  - **NEW:** GET /api/v1/profile/stats - Get reading statistics
- [x] Static Files Configuration
  - **NEW:** Mounted /static directory for avatar storage
  - **NEW:** Created static/avatars/ directory structure
  - **NEW:** Automated file cleanup and gitignore configuration
- [x] Unit Tests (tests/test_profile_crud.py)
  - 22+ comprehensive test cases covering all CRUD operations
  - Test profile retrieval and creation
  - Test profile updates (with real MongoDB data)
  - **NEW:** Test avatar file upload with validation
  - **NEW:** Test avatar URL updates
  - **NEW:** Test statistics aggregation from real session data
  - Test validation and error handling
  - Test authentication requirement
  - Test edge cases (non-existent users, partial updates, nested preferences)

#### Frontend Profile UI ✅ COMPLETE
- [x] Enhanced Profile Page Component (src/pages/ProfilePage.tsx)
  - Display current user information with live backend data
  - Profile settings form with save functionality
  - **NEW:** Avatar display with hover-to-edit functionality
  - **NEW:** Avatar upload modal with file upload and URL input
  - **NEW:** Reading statistics cards with real-time data
  - Voice preferences section
  - Reading preferences section
  - Interaction preferences section
  - Loading and error states
- [x] **NEW:** Avatar Management
  - Avatar image display (fallback to icon if no avatar)
  - File upload with drag-and-drop support
  - URL input for web-hosted images
  - Image validation (file type, size limits)
  - Upload progress and success feedback
  - Hover overlay with camera icon for easy editing
- [x] **NEW:** Reading Statistics Display
  - Books started counter with icon
  - Questions asked counter with icon
  - Total listening time (hours and minutes)
  - Color-coded stat cards with gradients
  - Real-time data from backend aggregation
- [x] **NEW:** React Query Hooks (src/hooks/useProfile.ts)
  - useProfile() - Fetch user profile with caching
  - useUpdateProfile() - Update basic profile info
  - useUploadAvatar() - Upload avatar file with progress
  - useUpdateAvatarUrl() - Set avatar from URL
  - useUpdateInteractionPreferences() - Update AI interaction settings
  - useProfileStats() - Fetch reading statistics
  - Automatic cache invalidation and optimistic updates
- [x] Voice Preferences
  - TTS provider selection (Coqui XTTS, OpenAI, ElevenLabs)
  - Voice selection (Nova, Alloy, Echo, Fable, Onyx, Shimmer)
  - Playback speed control (0.5x - 2.0x)
  - Language selection (10+ languages)
- [x] Reading Preferences
  - Reading level selection (beginner/intermediate/advanced)
  - Explanation depth (brief/detailed)
  - Discussion topics selection (themes, characters, context, symbolism, plot, setting)
- [x] Form Validation and Error Handling
  - Real-time backend updates
  - Error messages via toast notifications
  - Success notifications
  - Save button with loading state
- [x] **NEW:** Enhanced API Client (src/lib/api.ts)
  - profile.uploadAvatar() - File upload with FormData
  - profile.updateAvatarUrl() - URL-based avatar update
  - profile.updateInteractionPreferences() - Update AI interaction settings
  - profile.getStats() - Fetch user statistics
  - Full TypeScript typing for all profile methods

#### Integration Points ✅ COMPLETE
- [x] Leverages existing User model (backend/app/models/user.py)
- [x] Uses shared Supabase auth (apps/shared/auth/supabase_auth.py)
- [x] Frontend API client already supports profile methods
- [x] Backend service deployed and running

#### Deployment Status ✅ COMPLETE
- [x] Backend service restarted successfully
- [x] All profile endpoints functional
- [x] API documentation available at /api/docs
- [x] Unit tests passing (17/17)

---

## 🎉 Latest Update: User Signup & Authentication System (2025-11-12)

### ✅ BACKEND SIGNUP ENDPOINT IMPLEMENTED

**Implementation Summary**: Created backend authentication endpoints for user signup and login to handle Supabase email confirmation issues. Users can now create accounts directly through the InkWave API.

#### Backend Authentication Routes ✅ COMPLETE
- [x] Auth Routes Created (backend/app/api/routes/auth.py)
  - POST /api/v1/auth/signup - User registration endpoint
  - POST /api/v1/auth/login - User login endpoint
  - Automatic Supabase user creation
  - MongoDB profile initialization
  - Free trial credits allocation (200 credits = $2)
  - Wallet creation on signup
  - Proper error handling and logging

- [x] Constants Configuration (backend/app/config/constants.py)
  - FREE_TRIAL_CREDITS = 200
  - Pricing constants
  - Wallet settings
  - Configuration values

- [x] Integration with Main App
  - Auth router registered in main.py
  - Proper middleware configuration
  - CORS settings for signup/login
  - Error handling for email confirmation issues

#### Frontend Authentication Updates ✅ COMPLETE
- [x] API Client Enhanced (frontend/src/lib/api.ts)
  - auth.signup() method
  - auth.login() method
  - Proper TypeScript typing
  - Error response handling

- [x] Auth Store Updated (frontend/src/store/authStore.ts)
  - signUp() uses backend endpoint instead of direct Supabase call
  - Better error handling with detailed messages
  - Session management with backend response
  - Toast notifications for success/error states

#### Email Confirmation Fixed ✅
- **Solution Implemented**: Using Supabase service role key to create users with auto-confirmed emails
- **Method**: Admin API (`supabase_admin.auth.admin.create_user`) bypasses email confirmation requirement
- **Result**: Users can now sign up instantly without waiting for email confirmation
- **Testing**: Successfully created and logged in with test account (testuser3@inkwave.com)

#### Test Accounts Available 🔑
**New Users**: Can now create accounts directly via signup page!
- Email: Any valid email address
- Password: Minimum 6 characters
- Instant access with 200 free credits!

**Pre-configured Test Accounts**:
   - admin@ailabsafrica.com / Admin@2024!
   - user@ailabsafrica.com / User@2024!
   - alfred.anyan@gmail.com / AlfredSecure2024!

#### Deployment Status ✅ COMPLETE
- [x] Backend auth routes deployed
- [x] Backend service restarted successfully
- [x] Frontend built with new signup flow
- [x] API endpoints accessible at /api/v1/auth/signup and /api/v1/auth/login
- [x] **Email confirmation bypass implemented with service role key**
- [x] **Signup tested and working perfectly**
- [x] **Login tested and working perfectly**
- [x] Documentation updated

#### Technical Implementation Details
- **Supabase admin client** with service role key for bypassing email confirmation
- **Admin API** (`supabase_admin.auth.admin.create_user`) for user creation
- Auto-confirmed emails (`email_confirm: True`)
- Automatic sign-in after signup to provide session tokens
- User profile creation in MongoDB on signup
- Wallet service integration for free trial credits (200 credits = $2)
- Pydantic models for request/response validation
- Comprehensive error handling with HTTPException
- Logging for debugging and monitoring

---

## 🎉 Enhanced Profile Button & Navigation (2025-11-12)

### ✅ PROFILE BUTTON ENHANCEMENT COMPLETE

**Implementation Summary**: Enhanced header navigation with prominent profile button showing user avatar, personalization indicators, and improved dropdown menu for easy access to personalized profile settings.

#### Frontend Navigation Enhancement ✅ COMPLETE
- [x] Enhanced Profile Button (src/components/Header.tsx)
  - **Avatar Display**: Shows user's uploaded avatar or gradient fallback icon
  - **Personalization Indicator**: Green pulsing dot showing profile is personalized
  - **User Name Display**: Shows display name or email username
  - **Hover Effects**: Purple gradient border with shadow on hover
  - **Smooth Animations**: Dropdown menu with slide-in animation
  - **Responsive Design**: Hides name on mobile, shows only avatar

- [x] Improved Dropdown Menu
  - **User Info Header**: Shows full name and email at top
  - **Highlighted Profile Link**: "My Profile" with sparkles icon and subtitle
  - **Visual Hierarchy**: Icons and descriptions for all menu items
  - **Better Styling**: Purple gradient backgrounds and hover states
  - **Quick Access**: Direct links to Profile, Wallet, Admin, Sign Out

- [x] Profile Data Integration
  - Fetches user profile on header load
  - Displays avatar from backend
  - Shows display name or falls back to email
  - Real-time profile updates

#### Visual Features
- **Avatar Ring**: Purple ring around avatar for visual emphasis
- **Green Dot Indicator**: Animated pulse to show personalization active
- **Gradient Button**: Purple to pink gradient background (10% opacity)
- **Sparkles Icon**: Special icon for "My Profile" to emphasize personalization
- **Hover Glow**: Shadow glow effect on hover for premium feel
- **ChevronDown Icon**: Indicates dropdown menu availability

#### User Experience Improvements
- Users can now instantly see their profile picture in the header
- One-click access to personalized profile page
- Visual feedback showing profile is personalized
- Clear indication of current user
- Professional, modern appearance consistent with InkWave branding

#### Technical Implementation
- Added profile state management in Header component
- Integrated API call to fetch profile data
- TypeScript interface for UserProfile
- Proper error handling for profile loading
- Optimized rendering with conditional avatar display

#### Build Status ✅ COMPLETE
- [x] Frontend built successfully (6.42s)
- [x] No TypeScript errors
- [x] Bundle size: 787.26 kB (214.77 kB gzipped)
- [x] All components rendering correctly

---

## 🎉 Previous Update: Organization CRUD Complete (2025-11-04)

### ✅ ADMIN ORGANIZATION MANAGEMENT IMPLEMENTED

**Implementation Summary**: Full CRUD operations for organization management in the admin interface, including create, read, update, delete, and member management.

#### Backend Organization API ✅ COMPLETE
- [x] Organization CRUD Endpoints
  - POST /api/v1/organizations - Create organization
  - GET /api/v1/organizations - List user's organizations
  - GET /api/v1/organizations/{id} - Get organization details
  - PUT /api/v1/organizations/{id} - Update organization
  - DELETE /api/v1/organizations/{id} - Delete (deactivate) organization
- [x] Member Management Endpoints
  - GET /api/v1/organizations/{id}/members - List members
  - PUT /api/v1/organizations/{id}/members/{user_id} - Update member role
  - DELETE /api/v1/organizations/{id}/members/{user_id} - Remove member
- [x] Role-based Access Control
  - Admin/universal admin checks for update/delete operations
  - Member access verification
  - Self-removal prevention for last admin

#### Frontend Organization UI ✅ COMPLETE
- [x] Organization List View
  - Display all user organizations
  - Show organization cards with role badges
  - Real-time status indicators
- [x] Create Organization Modal
  - Form with name, display name, description, industry, website
  - Auto-generation of URL-safe organization names
  - Success/error handling with toast notifications
- [x] Edit Organization Modal
  - Update organization details
  - Validation and error handling
- [x] Delete Organization Confirmation
  - Confirmation dialog with warning
  - Soft delete (deactivation) implementation
- [x] Member Management Integration
  - Load and display organization members
  - Member role badges
  - API client methods configured

#### Unit Tests ✅ COMPLETE
- [x] Test Suite Created (test_organization_crud.py)
  - 12 comprehensive test cases
  - Tests for all CRUD operations
  - Member management tests
  - Access control tests
  - Edge case coverage

#### Deployment Status ✅ COMPLETE
- [x] Backend service restarted successfully
- [x] Frontend built without errors
- [x] All endpoints functional
- [x] API documentation available at /api/docs

---

## 🎉 Major Milestone: Backend Enhancement Complete (2025-11-03)

### ✅ ALL 5 PHASES IMPLEMENTED - BACKEND READY

**Implementation Summary**: All backend services for audiobook narration, voice Q&A, PDF processing, voice cloning, and multi-language support are complete and deployed.

#### Phase 1: Audio Narration ✅ COMPLETE
- [x] Enhanced TTS Service (525 lines)
  - Integration with TTSProviderService
  - 10+ TTS providers support
  - Automatic billing
  - Audio caching
  - Cost estimation
- [x] Audio Generation Endpoints (822 lines total in audio.py)
  - POST /api/v1/audio/chunks/{chunk_id} - Generate chunk audio
  - GET /api/v1/audio/chunks/{chunk_id} - Get cached audio
  - POST /api/v1/audio/books/{book_id}/chapters/{chapter_id} - Chapter narration
  - GET /api/v1/audio/books/{book_id}/estimate - Cost estimation
  - GET /api/v1/audio/providers - Available providers
  - DELETE /api/v1/audio/chunks/{chunk_id}/cache - Clear cache
- [x] Schema Updates
  - BookChunk: Added 8 audio-related fields
  - UserProfile: Added VoicePreferences model
- [x] Cost Model: $0.015 per 1000 chars (base), 2x for premium providers

#### Phase 2: Voice Q&A ✅ COMPLETE
- [x] ASR Service (210 lines)
  - Whisper-based transcription
  - 30+ language support
  - Automatic billing (~$0.006/min)
- [x] Voice Interaction Endpoints
  - POST /api/v1/interactions/{id}/voice-question - Send voice question
  - GET /api/v1/interactions/{id}/messages/{index}/audio - Get message audio
- [x] Full Flow: Voice upload → ASR → RAG → TTS response

#### Phase 3: PDF Upload & Processing ✅ COMPLETE
- [x] Book Processing Service Enhanced (335 lines)
  - PDF text extraction via DocumentProcessor
  - Automatic chapter detection
  - Smart chunking (1000 chars, 200 overlap)
  - Embedding generation
- [x] Upload Endpoints
  - POST /api/v1/books/upload - Upload PDF book
  - GET /api/v1/books/{book_id}/processing-status - Check status
- [x] Cost: ~$0.80 per 100-page book

#### Phase 4: Voice Cloning ✅ COMPLETE
- [x] Voice Clone Management Endpoints
  - POST /api/v1/audio/voice-clones - Upload reference audio
  - GET /api/v1/audio/voice-clones - List user clones
  - DELETE /api/v1/audio/voice-clones/{clone_id} - Delete clone
  - POST /api/v1/audio/voice-clones/{clone_id}/test - Test clone
- [x] Storage: /opt/kasaai/apps/inkwave/backend/storage/voice_clones/
- [x] MongoDB collection: voice_clones
- [x] Cost: +$0.05 per request with cloning

#### Phase 5: Multi-Language & Analytics ✅ COMPLETE
- [x] Multi-Language Support
  - GET /api/v1/audio/languages - List supported languages
  - POST /api/v1/audio/chunks/{chunk_id}/translate - Generate in target language
  - 17 languages via Coqui XTTS, 30+ via Whisper
- [x] Analytics Already Available
  - GET /api/v1/analytics/books/{book_id} - Book analytics
  - GET /api/v1/analytics/listening-stats - User stats
  - GET /api/v1/analytics/popular-books - Popular books

### 📊 Implementation Statistics
- **Total New Endpoints**: 20+
- **New Services**: 2 (TTS, ASR)
- **Enhanced Services**: 3 (Book processing, Interaction, Audio)
- **Code Added**: ~3000 lines
- **Documentation**: 1000+ lines (including IMPLEMENTATION_COMPLETE.md)
- **Supported Languages**: 17 (TTS), 30+ (ASR)
- **TTS Providers**: 10+

### 🚀 Deployment Status
- **Service**: kasaai-inkwave-backend.service
- **Status**: ✅ Active (running)
- **Port**: 30033
- **URL**: https://inkwave-api.ailabsafrica.com
- **Docs**: https://inkwave-api.ailabsafrica.com/api/docs

### 📝 Documentation Created
- [x] SHARED_SERVICES_ENHANCEMENT_PLAN.md (650 lines) - Detailed enhancement plan
- [x] IMPLEMENTATION_COMPLETE.md (900+ lines) - Comprehensive implementation summary

### ⏳ Pending (Future Work)
- [ ] Unit test suite creation (per coding guidelines)
- [ ] Integration tests
- [ ] Frontend implementation (React Native components)
- [ ] Performance benchmarks
- [ ] Load testing

---

## 🎯 Current Sprint: Project Setup & Planning

### Planning Phase (2025-10-23)
- [x] Define core concept and features
- [x] Create PLANNING.md with architecture
- [x] Update PLANNING.md with shared services integration
- [x] Create TASK.md for task tracking
- [ ] Create README.md with setup instructions
- [ ] Set up project structure
- [ ] Initialize git repository
- [ ] Document API endpoints

---

## 📋 Phase 1: MVP (4-6 weeks)

### Sprint 0: Shared Services Integration (Week 0)
**Goal**: Set up and integrate KasaAI shared services

✅ **Completed (2025-10-24)**:
- [x] RAG Service created (`apps/shared/integration/rag.py`)
- [x] Document Processor created (`apps/shared/integration/document_processor.py`)
- [x] Wallet Service created (`apps/shared/integration/wallet.py`)
- [x] Usage Calculator created (`apps/shared/integration/usage_calculator.py`)

**Integration Tasks**:
- [ ] Review shared services documentation in `apps/TASK.md`
- [ ] Test shared RAGService initialization
  - [ ] Create test collection for bookshop
  - [ ] Test document indexing
  - [ ] Test semantic search
  - [ ] Test confidence scoring
- [ ] Test shared DocumentProcessor
  - [ ] Test PDF extraction
  - [ ] Test chunking strategies
  - [ ] Test metadata extraction
- [ ] Test shared WalletService
  - [ ] Create test wallet
  - [ ] Test credit/debit operations
  - [ ] Test payment gateway (test mode)
  - [ ] Test transaction history
- [ ] Test shared UsageCalculator
  - [ ] Test RAG cost calculation
  - [ ] Test TTS/STT cost calculation
  - [ ] Test document processing cost
  - [ ] Test cost breakdown generation

---

### Sprint 1: Project Setup (Week 1)
**Goal**: Set up development environment and project structure

#### Backend Setup
- [ ] Create FastAPI project structure in `apps/core_backend/bookshop/`
  - [ ] Create `routes/` directory with initial files
  - [ ] Create `services/` directory
  - [ ] Create `models/` directory
  - [ ] Create `utils/` directory
  - [ ] Create `tests/` directory
  - [ ] Create `config.py` for settings
  - [ ] Create `main.py` for FastAPI app initialization
- [ ] Set up MongoDB connection
  - [ ] Add MongoDB credentials to `.env`
  - [ ] Create database connection utility
  - [ ] Test connection with health check endpoint
- [ ] Set up pgvector database
  - [ ] Create pgvector database
  - [ ] Create `book_embeddings` table
  - [ ] Create indexes
  - [ ] Add pgvector credentials to `.env`
- [ ] Set up Supabase authentication
  - [ ] Configure Supabase client
  - [ ] Create auth middleware
  - [ ] Test auth flow
- [ ] Create requirements.txt with initial dependencies
  - [ ] FastAPI, uvicorn
  - [ ] MongoDB driver (motor/pymongo) - **used by shared WalletService**
  - [ ] pgvector client (psycopg2/asyncpg) - **used by shared RAGService**
  - [ ] Pydantic
  - [ ] OpenAI client - **used by shared RAGService & UsageCalculator**
  - [ ] python-dotenv
  - [ ] **Shared services dependencies (see apps/shared/integration/):**
    - [ ] langchain, langchain-openai, langchain-google-genai, langchain-anthropic
    - [ ] PyPDF2, pdfplumber, python-docx (for DocumentProcessor)
    - [ ] stripe, requests (for WalletService payment gateways)

#### Frontend Setup
- [ ] Initialize React PWA project (Vite + React)
  - [ ] Set up project with TypeScript
  - [ ] Configure Tailwind CSS
  - [ ] Set up routing (react-router)
  - [ ] Create basic layout components
- [ ] Create API client utility
  - [ ] Axios setup with base URL
  - [ ] Auth token management
  - [ ] Error handling interceptors
- [ ] Set up Supabase auth in frontend
  - [ ] Supabase client configuration
  - [ ] Auth context/provider
  - [ ] Login/signup pages

#### Database Schema
- [ ] Create Pydantic models for MongoDB collections
  - [ ] `models/book.py` - Book model
  - [ ] `models/user.py` - User profile model (extends Supabase auth)
  - [ ] ~~`models/wallet.py` - **Use shared WalletService**~~
  - [ ] `models/session.py` - ReadingSession model
  - [ ] `models/interaction.py` - Interaction model
  - [ ] ~~`models/usage.py` - **Use shared UsageCalculator**~~
- [ ] Create database initialization scripts
  - [ ] MongoDB indexes for books, users, sessions
  - [ ] pgvector schema migration (for shared RAGService)
  - [ ] **Shared WalletService MongoDB indexes** (automatic via shared service)

#### Documentation
- [ ] Write README.md with setup instructions
- [ ] Document environment variables
- [ ] Create API documentation structure (FastAPI auto-docs)

---

### Sprint 2: User Authentication & Basic Book Management (Week 2)

#### Authentication
- [ ] Implement Supabase auth endpoints
  - [ ] POST `/api/bookshop/v1/auth/signup`
  - [ ] POST `/api/bookshop/v1/auth/login`
  - [ ] POST `/api/bookshop/v1/auth/logout`
  - [ ] GET `/api/bookshop/v1/auth/me` (current user)
- [ ] Create auth middleware for protected routes
- [ ] Frontend auth flow
  - [ ] Login page UI
  - [ ] Signup page UI
  - [ ] Protected route wrapper
  - [ ] Auth state management

#### Book CRUD (Admin)
- [ ] Create Book model and validation
- [ ] Implement book endpoints (routes/books.py)
  - [ ] GET `/api/bookshop/v1/books` - List books (with pagination, filters)
  - [ ] GET `/api/bookshop/v1/books/{book_id}` - Get book details
  - [ ] POST `/api/bookshop/v1/books` - Create book (admin only)
  - [ ] PUT `/api/bookshop/v1/books/{book_id}` - Update book (admin only)
  - [ ] DELETE `/api/bookshop/v1/books/{book_id}` - Delete book (admin only)
- [ ] Create book service (services/book_service.py)
  - [ ] CRUD operations
  - [ ] Search functionality
  - [ ] Pagination helper
- [ ] Frontend book browsing
  - [ ] Book list page
  - [ ] Book card component
  - [ ] Book detail page
  - [ ] Search/filter UI

#### Unit Tests
- [ ] Test auth endpoints
- [ ] Test book CRUD operations
- [ ] Test book model validation
- [ ] Test pagination logic

---

### Sprint 3: Wallet System & Usage Tracking (Week 3)
**Goal**: Integrate shared WalletService and UsageCalculator

#### Wallet Backend Integration (Using Shared Services)
- [ ] ~~Create Wallet models~~ - **Use `apps.shared.integration.wallet.WalletService`**
- [ ] Initialize shared WalletService in backend
  - [ ] Create wallet service instance: `await WalletService.create(mongodb_uri, database_name)`
  - [ ] Configure payment gateways (Stripe, Paystack)
  - [ ] Add environment variables (STRIPE_SECRET_KEY, PAYSTACK_SECRET_KEY)
- [ ] Implement wallet API wrapper (routes/wallet.py)
  - [ ] GET `/api/bookshop/v1/wallet` - Get balance via `wallet_service.get_wallet_by_user()`
  - [ ] POST `/api/bookshop/v1/wallet/topup/stripe` - Stripe top-up via `wallet_service.initiate_stripe_topup()`
  - [ ] POST `/api/bookshop/v1/wallet/topup/paystack` - Paystack top-up via `wallet_service.initiate_paystack_topup()`
  - [ ] GET `/api/bookshop/v1/wallet/transactions` - Transaction history via `wallet_service.get_transactions()`
  - [ ] Webhook endpoints for payment verification
- [ ] ~~Create billing service~~ - **Use shared WalletService directly**
  - [ ] Wrapper: `charge_user()` → `wallet_service.debit()`
  - [ ] Wrapper: `check_balance()` → `wallet_service.get_balance()`
- [ ] ~~Create cost calculator~~ - **Use `apps.shared.integration.usage_calculator.UsageCalculator`**
  - [ ] Initialize with user's pricing tier
  - [ ] Calculate costs using: `usage_calculator.calculate_rag_cost()`, `calculate_tts_cost()`, etc.
  - [ ] Get cost breakdown: `usage_calculator.get_cost_breakdown()`

#### Wallet Frontend
- [ ] Wallet balance display component (header)
  - [ ] Use `wallet.is_low_balance` for warning indicator
- [ ] Wallet page
  - [ ] Balance display with currency
  - [ ] Top-up form with amount options ($5, $10, $25, $50)
  - [ ] Payment gateway selection (Stripe/Paystack)
  - [ ] Transaction history table with filters
  - [ ] Cost breakdown visualization
- [ ] Low balance warning modal
  - [ ] Configurable threshold per user
  - [ ] Quick top-up button

#### Unit Tests (Shared Services Already Tested)
- [ ] Test wallet API wrapper endpoints
- [ ] Test payment webhook handling
- [ ] Test cost calculation wrapper functions
- [ ] Test frontend wallet components
- [ ] Integration test: user top-up → charge → transaction history flow

---

### Sprint 4: Basic Reading Experience (Week 4)

#### Book Chunking (Using Shared DocumentProcessor)
- [ ] ~~Create chunking utility~~ - **Use `apps.shared.integration.document_processor.DocumentProcessor`**
- [ ] Create admin script to process and chunk a sample book
  - [ ] Read PDF/text file
  - [ ] Use `document_processor.process_file()` for extraction and chunking
    - [ ] Choose chunking strategy (Paragraph-aware for MVP)
    - [ ] Extract metadata automatically
  - [ ] Save chunks to MongoDB `book_chunks` collection
  - [ ] Initialize RAG knowledge base via `rag_service.initialize_knowledge_base()`
  - [ ] Create embeddings automatically (pgvector)

#### Reading Session Backend
- [ ] Create ReadingSession model
- [ ] Implement reading endpoints (routes/reading.py)
  - [ ] POST `/api/bookshop/v1/reading/sessions` - Start reading session
  - [ ] GET `/api/bookshop/v1/reading/sessions/{session_id}` - Get session
  - [ ] PUT `/api/bookshop/v1/reading/sessions/{session_id}` - Update progress
  - [ ] POST `/api/bookshop/v1/reading/sessions/{session_id}/bookmark` - Add bookmark
  - [ ] GET `/api/bookshop/v1/reading/chunks/{chunk_id}` - Get chunk text
- [ ] Create reading service (services/reading_service.py)
  - [ ] Start session
  - [ ] Update progress
  - [ ] Get current chunk
  - [ ] Get next chunk

#### TTS Integration (Text Output Only for MVP)
- [ ] Create TTS service (services/tts_service.py)
  - [ ] OpenAI TTS integration
  - [ ] Generate audio for chunk
  - [ ] Cache audio files (S3/MinIO or local)
  - [ ] Return audio URL
- [ ] Add TTS endpoint
  - [ ] GET `/api/bookshop/v1/reading/chunks/{chunk_id}/audio` - Get/generate audio
  - [ ] Track usage and charge user

#### Reading UI
- [ ] Audio player component
  - [ ] Play/pause button
  - [ ] Progress bar
  - [ ] Speed control
  - [ ] Skip forward/back (next/previous chunk)
- [ ] Reading page
  - [ ] Display current chunk text
  - [ ] Audio player
  - [ ] Tap/swipe to advance
  - [ ] Chapter progress indicator
  - [ ] Bookmark button
- [ ] Fetch and queue audio chunks

#### Unit Tests
- [ ] Test reading session CRUD
- [ ] Test chunk retrieval
- [ ] Test progress updates
- [ ] Test TTS service (mock OpenAI)

---

### Sprint 5: Basic Q&A Interaction (Week 5-6)
**Goal**: Integrate shared RAGService for intelligent Q&A

#### Q&A Backend (Using Shared RAGService)
- [ ] Create Interaction model
- [ ] Implement interaction endpoints (routes/interaction.py)
  - [ ] POST `/api/bookshop/v1/interactions` - Start interaction session
  - [ ] POST `/api/bookshop/v1/interactions/{interaction_id}/messages` - Send message
  - [ ] GET `/api/bookshop/v1/interactions/{interaction_id}` - Get interaction history
- [ ] Create voice agent service (services/voice_agent.py)
  - [ ] Initialize shared RAGService for book collection
  - [ ] Query RAG using `rag_service.query_knowledge_base()`:
    - [ ] Pass user question
    - [ ] Include reading context metadata (current position, no spoilers filter)
    - [ ] Use custom system prompt (personalized book companion)
    - [ ] Get response with confidence score
  - [ ] Build enhanced prompt with:
    - System prompt (personalized book companion)
    - Retrieved book passages (from RAG)
    - Current reading context
    - User profile
    - User question
  - [ ] Handle low-confidence responses (< 0.7):
    - [ ] Prompt user for clarification
    - [ ] Escalate to broader search
  - [ ] Track usage via shared UsageCalculator:
    - [ ] Calculate RAG cost: `usage_calculator.calculate_rag_cost(input_tokens, output_tokens)`
    - [ ] Get total cost breakdown
  - [ ] Charge user via shared WalletService:
    - [ ] Debit wallet: `wallet_service.debit()` with idempotency key
    - [ ] Store transaction metadata

#### Q&A Frontend
- [ ] Q&A panel/modal on reading page
- [ ] Text input for questions
- [ ] Display conversation history
- [ ] Show cost per interaction
- [ ] "Ask a question" button

#### Unit Tests
- [ ] Test interaction CRUD
- [ ] Test voice agent service (mock LLM)
- [ ] Test message handling
- [ ] Test cost tracking

---

### Sprint 6: MVP Integration & Testing (Week 6)

#### Integration Testing
- [ ] End-to-end flow test
  - [ ] User signup → browse → start reading → ask question → check wallet
- [ ] Load test basic endpoints
- [ ] Fix critical bugs

#### Deployment
- [ ] Deploy backend to production server
  - [ ] Update kasaai-core-backend.service
  - [ ] Add bookshop routes to main FastAPI app
  - [ ] Restart service
- [ ] Deploy frontend PWA
  - [ ] Build production bundle
  - [ ] Deploy to CDN or static host
  - [ ] Configure nginx (if needed)

#### Documentation
- [ ] Update README with deployment instructions
- [ ] Create user guide (basic)
- [ ] Document known issues/limitations

---

## 📋 Phase 2: Enhanced Interaction (3-4 weeks)

### Voice Input & Output
- [ ] Implement STT (Whisper API)
  - [ ] Voice recording component (frontend)
  - [ ] STT endpoint in backend
  - [ ] Integrate with interaction flow
- [ ] Implement TTS for Q&A responses
  - [ ] TTS service integration
  - [ ] Audio delivery
  - [ ] Charge for TTS usage

### WebSocket Real-Time Communication
- [ ] Set up python-socketio in backend
- [ ] Create WebSocket events
  - [ ] `connect` / `disconnect`
  - [ ] `start_reading` - Join reading session
  - [ ] `advance_chunk` - Move to next chunk
  - [ ] `ask_question` - Send question, receive answer
  - [ ] `update_progress` - Save reading position
- [ ] Frontend WebSocket client
  - [ ] socket.io-client integration
  - [ ] Real-time progress sync
  - [ ] Real-time Q&A

### RAG-Powered Q&A (Already Integrated via Shared RAGService)
- [ ] ~~Create RAG service~~ - **Already using `apps.shared.integration.rag.RAGService`**
- [ ] Enhance RAG integration in voice agent
  - [ ] Fine-tune retrieval parameters (k, similarity_threshold)
  - [ ] Test retrieval accuracy with sample books
  - [ ] Optimize system prompts for better answers
  - [ ] Implement confidence-based response handling
  - [ ] Add support for multiple AI providers (OpenAI/Gemini/Anthropic)

### Session Persistence
- [ ] Save bookmarks to database
- [ ] Resume reading from last position
- [ ] Sync across devices (same user)

### User Profiles & Preferences
- [ ] Create user profile model
- [ ] Profile settings page
  - [ ] Voice preference
  - [ ] Playback speed
  - [ ] Reading level
  - [ ] Explanation depth
- [ ] Use profile in LLM prompts

### Unit Tests
- [ ] Test WebSocket events
- [ ] Test RAG retrieval
- [ ] Test STT/TTS integration
- [ ] Test session persistence

---

## 📋 Phase 3: PDF Processing (3-4 weeks)

### PDF Upload Flow
- [ ] File upload endpoint
  - [ ] POST `/api/bookshop/v1/upload` - Upload PDF
  - [ ] Validate file type, size
  - [ ] Store in S3/MinIO
  - [ ] Create book record with "pending" status
- [ ] Frontend upload page
  - [ ] File picker
  - [ ] Upload progress bar
  - [ ] Processing status display

### Async Processing Pipeline
- [ ] Set up Celery + Redis
  - [ ] Install dependencies
  - [ ] Configure Celery app
  - [ ] Create worker service
- [ ] Create PDF processing task (tasks/process_pdf.py)
  - [ ] **Use shared DocumentProcessor**: `document_processor.process_file(pdf_path)`
    - [ ] Automatic text extraction (PyPDF2/pdfplumber with OCR fallback)
    - [ ] Automatic metadata extraction (author, page count, word count)
    - [ ] Smart chunking with 4 strategies available
    - [ ] Content cleanup and normalization (built-in)
  - [ ] **Use shared RAGService** for embeddings:
    - [ ] Initialize knowledge base: `rag_service.initialize_knowledge_base(collection_name, documents)`
    - [ ] Automatic vector embedding generation
    - [ ] Store in pgvector
  - [ ] **Calculate processing cost** via shared UsageCalculator:
    - [ ] `usage_calculator.calculate_document_processing_cost(num_pages, file_size_mb)`
  - [ ] **Charge user** via shared WalletService:
    - [ ] `wallet_service.debit()` for processing fee
  - [ ] Auto-generate metadata (LLM) - **custom logic, not in shared services**:
    - [ ] Generate summary (250 words)
    - [ ] Extract themes/topics
    - [ ] Extract characters (if fiction)
    - [ ] Estimate reading time
    - [ ] Determine difficulty level
  - [ ] Update book status to "ready"
- [ ] Processing status endpoint
  - [ ] GET `/api/bookshop/v1/books/{book_id}/processing-status`
  - [ ] WebSocket event for completion

### PDF Processor Service Enhancement
- [ ] ~~Create PDF processor~~ - **Use shared DocumentProcessor**
- [ ] Create metadata generation service (services/metadata_generator.py)
  - [ ] `generate_summary(text) -> str` (LLM-based)
  - [ ] `extract_themes(text) -> [str]` (LLM-based)
  - [ ] `extract_characters(text) -> [str]` (LLM-based for fiction)
  - [ ] `estimate_reading_time(word_count) -> int` (calculation-based)
  - [ ] `determine_difficulty(text) -> str` (LLM-based)
  - [ ] Track LLM usage via UsageCalculator

### Error Handling
- [ ] Retry logic for failures
- [ ] Manual review queue for failed uploads
- [ ] Refund processing fees on failure

### Unit Tests
- [ ] Test PDF extraction
- [ ] Test chunking logic
- [ ] Test metadata generation (mock LLM)
- [ ] Test Celery task

---

## 📋 Phase 4: Personalization (2-3 weeks)

### Interaction Memory
- [ ] Store all user interactions
  - [ ] Save messages to `interactions` collection
  - [ ] Link to user profile
- [ ] Retrieve past interactions
  - [ ] Include in LLM context (recent conversations)
  - [ ] Detect patterns (confusion topics, favorite themes)

### Adaptive Learning Level
- [ ] Track comprehension signals
  - [ ] Follow-up questions
  - [ ] Explicit user feedback ("too complex", "too simple")
- [ ] Adjust explanation depth dynamically
- [ ] Update user profile reading level

### Reading History Analysis
- [ ] Track completed books
- [ ] Analyze genres/themes read
- [ ] Build user interest profile

### Personalized Recommendations
- [ ] Simple recommendation endpoint
  - [ ] GET `/api/bookshop/v1/recommendations`
  - [ ] Based on reading history
  - [ ] Based on genre preferences
- [ ] Display on homepage

### Unit Tests
- [ ] Test memory retrieval
- [ ] Test adaptive prompts
- [ ] Test recommendation logic

---

## 📋 Phase 5: Scaling & Polish (3-4 weeks)

### Native Mobile Apps
- [ ] Migrate to React Native (Expo)
  - [ ] Port PWA components
  - [ ] Native audio player (Expo AV)
  - [ ] Native voice recording
  - [ ] Push notifications (low balance, book ready)
- [ ] iOS app
  - [ ] Build & test
  - [ ] App Store submission
- [ ] Android app
  - [ ] Build & test
  - [ ] Play Store submission

### Audio Caching & Optimization
- [ ] Pre-generate audio for narration
  - [ ] Background job to TTS all chunks
  - [ ] Store in CDN
- [ ] Audio streaming (chunked delivery)
- [ ] Adaptive bitrate

### Background Playback
- [ ] Android background service
- [ ] iOS background audio
- [ ] Notification controls

### Offline Mode
- [ ] Download books for offline reading
- [ ] Sync progress when online
- [ ] Cache audio locally

### Multi-Voice Support
- [ ] Add voice selection to user profile
- [ ] Integrate multiple TTS providers
  - [ ] ElevenLabs (premium)
  - [ ] OpenAI TTS (standard)
  - [ ] Google TTS (budget)
- [ ] Voice preview on profile page

### Payment Gateway Integration (Already in Shared WalletService)
- [ ] ~~Stripe integration~~ - **Already integrated in shared WalletService**
  - [ ] Use `wallet_service.initiate_stripe_topup()` for checkout
  - [ ] Webhook already handled by shared service
  - [ ] Just implement wrapper endpoints in routes/wallet.py
- [ ] ~~Paystack integration~~ - **Already integrated in shared WalletService**
  - [ ] Use `wallet_service.initiate_paystack_topup()` for African payments
  - [ ] Verify payments via `wallet_service.verify_paystack_payment()`
- [ ] Add frontend payment flow
  - [ ] Gateway selection UI
  - [ ] Redirect to payment URL
  - [ ] Handle payment success/failure callbacks

### Analytics Dashboard (Admin)
- [ ] Admin panel
  - [ ] User stats (DAU, retention)
  - [ ] Revenue metrics (ARPU, top-ups)
  - [ ] Cost metrics (LLM, TTS usage)
  - [ ] Book stats (most read, completion rate)
- [ ] Visualizations (charts)

### Unit Tests & E2E Tests
- [ ] Comprehensive test coverage
- [ ] E2E tests for critical flows
- [ ] Load testing

---

## 🐛 Bug Tracking

### Known Issues
_(None yet)_

---

## 💡 Discovered During Work

_(Tasks discovered during implementation will be added here)_

---

## 📝 Notes

- All new features require unit tests (see PLANNING.md)
- Update README when dependencies change
- Mark tasks complete immediately after finishing
- Always test CRUD operations with real data

---

**Last Updated**: 2025-10-23
