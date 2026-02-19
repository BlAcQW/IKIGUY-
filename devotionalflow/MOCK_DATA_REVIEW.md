# DevotionalFlow - Mock Data & Incomplete Integration Review

**Date:** December 21, 2025  
**Status:** Complete Review

## Executive Summary

This document identifies all components using mock data and features that are not fully wired up to the backend API in the DevotionalFlow application.

---

## 🔴 **COMPONENTS USING MOCK DATA**

### 1. **Admin Pages**

#### **UserManagement.tsx** (`frontend/src/pages/admin/UserManagement.tsx`)
- **Status:** ❌ **FULLY MOCK DATA**
- **Issue:** Uses hardcoded `mockUsers` array (8 fake users)
- **Backend Available:** ✅ `/api/v1/admin/users` endpoint exists and is implemented
- **Action Required:** Replace mock data with API call to `apiClient.client.get('/admin/users')`
- **Lines:** 65-141 (mockUsers definition), 150 (filteredUsers uses mockUsers)

#### **AdminAnalytics.tsx** (`frontend/src/pages/admin/AdminAnalytics.tsx`)
- **Status:** ❌ **FULLY MOCK DATA**
- **Issue:** Hardcoded analytics data (totalViews, viewsChange, topDevotionals, topAuthors)
- **Backend Available:** ✅ Analytics endpoints exist (`/api/v1/analytics/dashboard`, etc.)
- **Action Required:** 
  - Uncomment line 129: `const data = await apiClient.getAdminAnalytics(parseInt(timeRange));`
  - Remove hardcoded `analytics` state initialization (lines 93-118)
- **Note:** `AdminAnalyticsEnhanced.tsx` is properly wired up and should be used instead

### 2. **Author Pages**

#### **DevotionalManagement.tsx** (`frontend/src/pages/author/DevotionalManagement.tsx`)
- **Status:** ❌ **FULLY MOCK DATA**
- **Issue:** Uses hardcoded `mockDevotionals` array (6 fake devotionals)
- **Backend Available:** ✅ `/api/v1/author/devotionals` endpoint exists
- **Action Required:** Replace with `apiClient.client.get('/author/devotionals')` or use existing `apiClient.getDevotionals()` with author filter
- **Lines:** 79-147 (mockDevotionals definition), 220 (filteredDevotionals uses mockDevotionals)

### 3. **Discussion Features**

#### **Discussions.tsx** (`frontend/src/pages/Discussions.tsx`)
- **Status:** ❌ **FULLY MOCK DATA**
- **Issue:** Returns hardcoded discussion array (3 fake discussions)
- **Backend Available:** ❌ **NO BACKEND ENDPOINT**
- **Action Required:** 
  - Create backend route: `/api/v1/discussions` 
  - Implement discussion model and service
  - Wire up frontend to use real API
- **Lines:** 45-89 (mock data in queryFn)
- **Comment:** Line 46 says "When backend is ready, use: apiClient.get('/discussions', { params: { search: searchQuery } })"

---

## 🟡 **PARTIALLY WIRED / INCOMPLETE FEATURES**

### 1. **Reading Progress Tracking**

#### **SeriesDetail.tsx** (`frontend/src/pages/SeriesDetail.tsx`)
- **Status:** 🟡 **INCOMPLETE**
- **Issue:** 
  - Line 88: `const nextUnreadDevotional = publishedDevotionals[0]; // TODO: Track reading progress`
  - Line 253: `const isRead = false; // TODO: Track reading progress`
- **Backend Status:** Reading history exists (`/api/v1/users/me/history`) but progress tracking not implemented
- **Action Required:** 
  - Implement reading progress tracking in backend
  - Update frontend to check reading history to determine `isRead` status
  - Calculate `nextUnreadDevotional` based on reading progress

#### **Devotional.tsx** (`frontend/src/pages/Devotional.tsx`)
- **Status:** 🟡 **INCOMPLETE**
- **Issue:** 
  - Line 878: `// TODO: Fetch prev/next IDs from API or query cache`
  - `prevId` and `nextId` are `undefined` in SwipeableDevotionalView
- **Action Required:** 
  - Implement logic to fetch previous/next devotional IDs
  - Could use query cache or add API endpoint for navigation

### 2. **Gamification Features**

#### **gamification.py** (`backend/app/routes/gamification.py`)
- **Status:** 🟡 **PARTIALLY IMPLEMENTED**
- **Issues:**
  - Line 231: `change_from_yesterday=0  # TODO: Calculate daily change` (leaderboard)
  - Line 238: `# TODO: Implement friends leaderboard` (returns 501 Not Implemented)
  - Line 245: `# TODO: Implement weekly challenge leaderboard` (returns 501 Not Implemented)
  - Line 371: `"progress": 0  # TODO: Track actual progress` (achievement progress)
- **Action Required:**
  - Calculate daily change in leaderboard
  - Implement friends leaderboard (requires friend system)
  - Implement weekly challenge leaderboard
  - Track actual achievement progress

### 3. **UI Components**

#### **SeriesEditorDialog.tsx** (`frontend/src/components/series/SeriesEditorDialog.tsx`)
- **Status:** 🟡 **INCOMPLETE**
- **Issue:** 
  - Line 277: `// TODO: Open image picker`
  - Image picker button shows "Coming Soon" toast
- **Action Required:** Integrate image picker (ImageSearchDialog or upload)

---

## 🟢 **FULLY WIRED COMPONENTS**

### ✅ **Core Features (Fully Integrated)**
- **Devotionals:** Create, read, update, delete - ✅ Fully wired
- **Series:** Create, manage, schedule - ✅ Fully wired
- **Comments:** Post, reply, delete - ✅ Fully wired
- **Engagement:** Like, bookmark, share - ✅ Fully wired
- **Groups:** Create, join, leave, messages - ✅ Fully wired
- **Gamification:** Profile, streaks, achievements (basic) - ✅ Fully wired
- **Analytics:** AdminAnalyticsEnhanced.tsx - ✅ Fully wired
- **Calendar:** View, schedule, gaps - ✅ Fully wired
- **Moderation:** Flag, review, resolve - ✅ Fully wired
- **Media:** Image upload, Pexels search - ✅ Fully wired
- **Bible API:** Scripture lookup (API.Bible + ESV) - ✅ Fully wired
- **Notifications:** Push notifications, reminders - ✅ Fully wired
- **Auth:** Login, signup, profile - ✅ Fully wired

---

## 📋 **ACTION ITEMS SUMMARY**

### **High Priority (Mock Data)**
1. **UserManagement.tsx** - Replace mockUsers with `/api/v1/admin/users`
2. **DevotionalManagement.tsx** - Replace mockDevotionals with `/api/v1/author/devotionals`
3. **Discussions.tsx** - Create backend endpoint and wire up frontend

### **Medium Priority (Incomplete Features)**
4. **AdminAnalytics.tsx** - Use AdminAnalyticsEnhanced.tsx instead (already wired)
5. **Reading Progress** - Implement tracking in SeriesDetail and Devotional pages
6. **Prev/Next Navigation** - Implement in Devotional.tsx

### **Low Priority (Nice to Have)**
7. **Gamification TODOs** - Friends leaderboard, weekly challenges, progress tracking
8. **SeriesEditorDialog** - Image picker integration

---

## 🔍 **BACKEND ENDPOINTS STATUS**

### ✅ **Implemented & Working**
- `/api/v1/admin/users` - User list, role/status updates
- `/api/v1/author/devotionals` - Author's devotionals list
- `/api/v1/analytics/*` - All analytics endpoints
- `/api/v1/gamification/*` - Gamification (except friends/weekly leaderboards)
- `/api/v1/devotionals/*` - All devotional CRUD
- `/api/v1/series/*` - All series management
- `/api/v1/groups/*` - All group features
- `/api/v1/comments/*` - All comment features
- `/api/v1/engagement/*` - All engagement features

### ❌ **Missing Backend Endpoints**
- `/api/v1/discussions` - **NOT IMPLEMENTED** (Discussions feature needs backend)

---

## 📊 **STATISTICS**

- **Total Mock Data Components:** 3
- **Partially Wired Components:** 4
- **Fully Wired Components:** 15+
- **Missing Backend Endpoints:** 1 (discussions)

---

## 🎯 **RECOMMENDATIONS**

1. **Immediate:** Replace mock data in UserManagement and DevotionalManagement
2. **Short-term:** Create discussions backend endpoint
3. **Medium-term:** Implement reading progress tracking
4. **Long-term:** Complete gamification features (friends, weekly challenges)

