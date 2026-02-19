# Frontend ↔ Backend API Mapping Analysis

**Date**: 2025-10-22
**Backend**: African Language Community Platform API
**Frontend**: frontend-main (React + TypeScript)
**Backend Server**: http://localhost:8020
**Production API**: https://language-community-api.ailabsafrica.com

---

## 📊 Summary Statistics

- **Total Backend API Endpoints**: 140+
- **Frontend Pages**: 13
- **Frontend Routes**: 14
- **Pages Using Real API**: 9
- **Pages Using Mock Data**: 10+
- **Backend Endpoints Actually Called**: ~15

---

## 🔌 Backend API Endpoints (Complete List)

### 1. Authentication (`/api/v1/auth`)
```
✅ DELETE /api/v1/auth/account
✅ GET    /api/v1/auth/profile
✅ GET    /api/v1/auth/profile/{user_id}
✅ POST   /api/v1/auth/login
✅ POST   /api/v1/auth/logout
✅ POST   /api/v1/auth/refresh-token
✅ POST   /api/v1/auth/register
✅ PUT    /api/v1/auth/profile
```

### 2. Languages (`/api/v1/languages`)
```
✅ GET    /api/v1/languages/
✅ GET    /api/v1/languages/families
✅ GET    /api/v1/languages/families/{family_id}
✅ GET    /api/v1/languages/families/{family_id}/languages
✅ GET    /api/v1/languages/featured
✅ GET    /api/v1/languages/notebooks/file/{language_code}/{filename}
✅ GET    /api/v1/languages/search
✅ GET    /api/v1/languages/stats
✅ GET    /api/v1/languages/stats/overview
✅ GET    /api/v1/languages/{language_code}
✅ GET    /api/v1/languages/{language_code}/notebooks
✅ POST   /api/v1/languages/families
✅ POST   /api/v1/languages
```

### 3. ML Models (`/api/v1/models`) - **NEW MLOps Platform**
```
✅ GET    /api/v1/models
✅ GET    /api/v1/models/search
✅ GET    /api/v1/models/stats
✅ GET    /api/v1/models/{model_uuid}
✅ GET    /api/v1/models/{model_uuid}/download
✅ POST   /api/v1/models
✅ POST   /api/v1/models/{model_uuid}/issues
✅ POST   /api/v1/models/{model_uuid}/versions
✅ PUT    /api/v1/models/{model_uuid}
✅ DELETE /api/v1/models/{model_uuid}
```

### 4. Training Pipelines (`/api/v1/pipelines`) - **NEW MLOps Platform**
```
✅ GET    /api/v1/pipelines
✅ GET    /api/v1/pipelines/stats
✅ GET    /api/v1/pipelines/{pipeline_id}
✅ GET    /api/v1/pipelines/{pipeline_id}/metrics
✅ POST   /api/v1/pipelines
✅ POST   /api/v1/pipelines/{pipeline_id}/artifacts
✅ POST   /api/v1/pipelines/{pipeline_id}/complete
✅ PUT    /api/v1/pipelines/{pipeline_id}
✅ PUT    /api/v1/pipelines/{pipeline_id}/stages/{stage_name}
```

### 5. Dataset Versions (`/api/v1/datasets`) - **NEW MLOps Platform**
```
✅ GET    /api/v1/datasets/{dataset_id}/versions
✅ GET    /api/v1/datasets/{dataset_id}/versions/compare
✅ GET    /api/v1/datasets/{dataset_id}/versions/{version}
✅ GET    /api/v1/datasets/{dataset_id}/versions/{version}/compatible
✅ GET    /api/v1/datasets/{dataset_id}/versions/{version}/download
✅ POST   /api/v1/datasets/{dataset_id}/versions
✅ POST   /api/v1/datasets/{dataset_id}/versions/{version}/increment
✅ PUT    /api/v1/datasets/{dataset_id}/versions/{version}
```

### 6. External Resources (`/api/v1/resources`) - **NEW MLOps Platform**
```
✅ GET    /api/v1/resources/links
✅ GET    /api/v1/resources/links/{link_uuid}
✅ GET    /api/v1/resources/stats
✅ GET    /api/v1/resources/uploads
✅ GET    /api/v1/resources/uploads/{upload_uuid}
✅ POST   /api/v1/resources/links
✅ POST   /api/v1/resources/links/{link_uuid}/click
✅ POST   /api/v1/resources/links/{link_uuid}/verify
✅ POST   /api/v1/resources/links/{link_uuid}/vote
✅ POST   /api/v1/resources/upload
✅ PUT    /api/v1/resources/links/{link_uuid}
```

### 7. Discovery (`/api/v1/discovery`) - **NEW MLOps Platform**
```
✅ GET    /api/v1/discovery/languages/{language_code}
✅ GET    /api/v1/discovery/languages/{language_code}/datasets
✅ GET    /api/v1/discovery/languages/{language_code}/models
✅ GET    /api/v1/discovery/languages/{language_code}/resources
✅ GET    /api/v1/discovery/overview
✅ GET    /api/v1/discovery/recommendations/datasets/{dataset_uuid}/compatible-models
✅ GET    /api/v1/discovery/recommendations/models/{model_uuid}/similar
✅ GET    /api/v1/discovery/search
✅ GET    /api/v1/discovery/tasks/{task_type}
✅ GET    /api/v1/discovery/trending/datasets
✅ GET    /api/v1/discovery/trending/models
✅ GET    /api/v1/discovery/trending/resources
```

### 8. Submissions (`/api/v1/submit`)
```
✅ GET    /api/v1/submit/history
✅ GET    /api/v1/submit/language/{language_code}/browse
✅ GET    /api/v1/submit/stats/overview
✅ GET    /api/v1/submit/{submission_id}
✅ POST   /api/v1/submit/audio
✅ POST   /api/v1/submit/link
✅ POST   /api/v1/submit/text
✅ PUT    /api/v1/submit/{submission_id}
✅ DELETE /api/v1/submit/{submission_id}
```

### 9. Validation (`/api/v1/validate`)
```
✅ GET    /api/v1/validate/consensus/{submission_id}
✅ GET    /api/v1/validate/my-reviews
✅ GET    /api/v1/validate/pending
✅ GET    /api/v1/validate/queue/summary
✅ GET    /api/v1/validate/stats/validator
✅ POST   /api/v1/validate/dispute/{validation_id}
✅ POST   /api/v1/validate/promote/{submission_id}
✅ POST   /api/v1/validate/{submission_id}
```

### 10. Community (`/api/v1/community`)
```
✅ GET    /api/v1/community/achievements
✅ GET    /api/v1/community/achievements/user
✅ GET    /api/v1/community/activity/feed
✅ GET    /api/v1/community/languages/{language_code}/contributors
✅ GET    /api/v1/community/leaderboard
✅ GET    /api/v1/community/proposals
✅ GET    /api/v1/community/stats/engagement
✅ POST   /api/v1/community/gamification/award-points
✅ POST   /api/v1/community/proposals
✅ POST   /api/v1/community/proposals/{proposal_id}/vote
```

### 11. Governance (`/api/v1/governance`)
```
✅ GET    /api/v1/governance/disputes
✅ GET    /api/v1/governance/guidelines
✅ GET    /api/v1/governance/moderation/dashboard
✅ GET    /api/v1/governance/moderation/stats
✅ POST   /api/v1/governance/disputes
✅ POST   /api/v1/governance/disputes/{dispute_id}/vote
✅ POST   /api/v1/governance/moderation/actions
✅ POST   /api/v1/governance/reports
✅ PUT    /api/v1/governance/disputes/{dispute_id}
```

### 12. Notebooks (`/api/v1/notebooks`)
```
✅ GET    /api/v1/notebooks/categories/
✅ GET    /api/v1/notebooks/featured/
✅ GET    /api/v1/notebooks/languages/{language_code}/notebooks
✅ GET    /api/v1/notebooks/my/notebooks
✅ GET    /api/v1/notebooks/search
✅ GET    /api/v1/notebooks/trending/
✅ GET    /api/v1/notebooks/{notebook_id}
✅ GET    /api/v1/notebooks/{notebook_id}/comments
✅ GET    /api/v1/notebooks/{notebook_id}/download
✅ POST   /api/v1/notebooks/
✅ POST   /api/v1/notebooks/{notebook_id}/bookmark
✅ POST   /api/v1/notebooks/{notebook_id}/comments
✅ POST   /api/v1/notebooks/{notebook_id}/publish
✅ POST   /api/v1/notebooks/{notebook_id}/versions
✅ POST   /api/v1/notebooks/{notebook_id}/vote
✅ PUT    /api/v1/notebooks/{notebook_id}
```

### 13. Datasets (External Integration) (`/api/v1/datasets`)
```
✅ GET    /api/v1/datasets/
✅ GET    /api/v1/datasets/stats/overview
✅ GET    /api/v1/datasets/{dataset_id}
✅ GET    /api/v1/datasets/{dataset_id}/download
✅ GET    /api/v1/datasets/{dataset_id}/jobs
✅ GET    /api/v1/datasets/{dataset_id}/manifest
✅ POST   /api/v1/datasets/
✅ POST   /api/v1/datasets/common-voice
✅ POST   /api/v1/datasets/masakhane
✅ POST   /api/v1/datasets/openslr
✅ POST   /api/v1/datasets/{dataset_id}/pause
✅ POST   /api/v1/datasets/{dataset_id}/process
✅ DELETE /api/v1/datasets/{dataset_id}
```

---

## 🖥️ Frontend Pages & Routes

### Pages with API Integration

| Page | Route | API Integration | Status |
|------|-------|-----------------|--------|
| **Index** | `/` | ❌ None | Static homepage |
| **Dashboard** | `/dashboard` | 🟡 Mixed (Mock + Supabase) | Partially connected |
| **Languages** | `/languages` | 🟢 Real API | Connected |
| **LanguageDetail** | `/languages/:code` | 🟢 Real API | **WORKING** |
| **LanguageFamilyDetail** | `/languages/families/:id` | 🟢 Real API | **WORKING** |
| **Submit** | `/submit` | 🟡 Mock Data | Not connected |
| **Validate** | `/validate` | 🟡 Mock Data | Not connected |
| **Community** | `/community` | 🟡 Mock Data | Not connected |
| **Moderation** | `/moderation` | 🟡 Mock Data | Not connected |
| **Datasets** | `/datasets` | 🟡 Mock Data | Not connected |
| **Search** | `/search` | 🟡 Mock Data | Not connected |
| **Profile** | `/profile` | 🟡 Mixed (Supabase) | Partially connected |

---

## 🔗 Actual Frontend → Backend Connections

### ✅ **WORKING CONNECTIONS**

1. **LanguageDetail Page** → Backend API
   ```
   GET /api/v1/languages/{languageCode}
   GET /api/v1/languages/{languageCode}/notebooks
   ```
   - **Status**: ✅ Working
   - **Tested**: Yes

2. **LanguageFamilyDetail Page** → Backend API
   ```
   GET /api/v1/languages/families/{familyId}
   GET /api/v1/languages/families/{familyId}/languages
   ```
   - **Status**: ✅ Working
   - **Tested**: Yes

### 🟡 **PARTIAL CONNECTIONS** (Using Supabase)

3. **Dashboard** → Supabase + Some Mock
   - Uses Supabase for user data
   - Uses mock data for stats

4. **Profile** → Supabase
   - Uses Supabase for authentication and profile
   - Not using backend `/api/v1/auth` endpoints

### ❌ **NOT CONNECTED** (Using Mock Data)

5. **Submit Page** → ❌ Not using backend
   - Should use: `POST /api/v1/submit/audio`, `POST /api/v1/submit/text`
   - Currently: Mock data

6. **Validate Page** → ❌ Not using backend
   - Should use: `GET /api/v1/validate/pending`, `POST /api/v1/validate/{id}`
   - Currently: Mock data

7. **Community Page** → ❌ Not using backend
   - Should use: `GET /api/v1/community/leaderboard`, `GET /api/v1/community/achievements`
   - Currently: Mock data

8. **Moderation Page** → ❌ Not using backend
   - Should use: `GET /api/v1/governance/moderation/dashboard`
   - Currently: Mock data

9. **Datasets Page** → ❌ Not using backend
   - Should use: `GET /api/v1/datasets/`
   - Currently: Mock data

10. **Search** → ❌ Not using backend
    - Should use: `GET /api/v1/languages/search` or `GET /api/v1/discovery/search`
    - Currently: Mock data

---

## 🚫 Unused Backend APIs

### **NEVER CALLED BY FRONTEND**

#### MLOps Platform Endpoints (ALL UNUSED)
```
❌ /api/v1/models/* (10 endpoints)
❌ /api/v1/pipelines/* (9 endpoints)
❌ /api/v1/datasets/{id}/versions/* (8 endpoints)
❌ /api/v1/resources/* (11 endpoints)
❌ /api/v1/discovery/* (12 endpoints)
```
**Total**: ~50 NEW endpoints with ZERO frontend integration

#### Community Platform Endpoints (UNUSED)
```
❌ /api/v1/auth/* (8 endpoints) - Using Supabase instead
❌ /api/v1/submit/* (9 endpoints) - Using mock data
❌ /api/v1/validate/* (7 endpoints) - Using mock data
❌ /api/v1/community/* (10 endpoints) - Using mock data
❌ /api/v1/governance/* (9 endpoints) - Using mock data
❌ /api/v1/notebooks/* (16 endpoints) - Using mock data
❌ /api/v1/datasets/* (13 endpoints) - Using mock data
```
**Total**: ~72 existing endpoints with no frontend integration

---

## 📋 Integration Status Summary

### Backend API Coverage

| Category | Total Endpoints | Called by Frontend | Usage % |
|----------|----------------|-------------------|---------|
| **Authentication** | 8 | 0 | 0% |
| **Languages** | 13 | 5 | 38% |
| **ML Models** | 10 | 0 | 0% |
| **Pipelines** | 9 | 0 | 0% |
| **Dataset Versions** | 8 | 0 | 0% |
| **Resources** | 11 | 0 | 0% |
| **Discovery** | 12 | 0 | 0% |
| **Submissions** | 9 | 0 | 0% |
| **Validation** | 7 | 0 | 0% |
| **Community** | 10 | 0 | 0% |
| **Governance** | 9 | 0 | 0% |
| **Notebooks** | 16 | 0 | 0% |
| **Datasets** | 13 | 0 | 0% |
| **TOTAL** | **140+** | **~5** | **~4%** |

---

## 🎯 Recommendations

### High Priority - Connect Existing Features

1. **Submit Page** → Backend API
   - Replace mock data with real API calls
   - Connect to `/api/v1/submit/*` endpoints

2. **Validate Page** → Backend API
   - Implement validation queue
   - Connect to `/api/v1/validate/*` endpoints

3. **Community Features** → Backend API
   - Leaderboard, achievements, activity feed
   - Connect to `/api/v1/community/*` endpoints

4. **Authentication** → Consider Backend API
   - Currently using Supabase
   - Backend has full auth system at `/api/v1/auth/*`
   - **Decision needed**: Keep Supabase or migrate to backend?

### Medium Priority - New MLOps Features

5. **Add MLOps Dashboard**
   - Create new pages for Models, Pipelines, Resources
   - Utilize all `/api/v1/models/*`, `/api/v1/pipelines/*` endpoints

6. **Add Discovery Features**
   - Trending models/datasets
   - Search and recommendations
   - Connect to `/api/v1/discovery/*` endpoints

### Low Priority

7. **Datasets Page** → Backend Integration
   - External dataset integration (CommonVoice, OpenSLR)
   - Connect to `/api/v1/datasets/*` endpoints

8. **Notebooks** → Backend Integration
   - Jupyter notebook management
   - Connect to `/api/v1/notebooks/*` endpoints

---

## 🔍 Code Locations

### Backend
- **Server**: `http://localhost:8020`
- **Code**: `/opt/kasaai/apps/community/backend/`
- **Routes**: `/opt/kasaai/apps/community/backend/routes/`
- **Routers**: `/opt/kasaai/apps/community/backend/routers/`

### Frontend
- **Active Frontend**: `/opt/kasaai/apps/community/frontend-main/`
- **API Client**: `/opt/kasaai/apps/community/frontend-main/src/lib/api.ts`
- **Real API Client**: `/opt/kasaai/apps/community/frontend-main/src/lib/realApi.ts`
- **Pages**: `/opt/kasaai/apps/community/frontend-main/src/pages/`

---

## 📝 Notes

1. **Dual API Strategy**: Frontend uses both Supabase (for auth) and custom backend API (for languages)
2. **Mock Data Prevalence**: Most pages still use mock data instead of real API
3. **New MLOps Platform**: 50+ endpoints built but not integrated into frontend
4. **API Base URL**: Hardcoded to `https://language-community-api.ailabsafrica.com/api/v1`
5. **Local Testing**: Backend running on `http://localhost:8020` (port 8020, not 8001)

---

**Generated**: 2025-10-22
**Backend Status**: ✅ Running on port 8020
**Frontend Status**: 🟡 Partially integrated (only 4% of endpoints used)
