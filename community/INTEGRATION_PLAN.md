# Frontend-Backend Integration Implementation Plan

**Created**: 2025-10-22
**Duration**: 4 weeks (Week 11-14)
**Goal**: Connect frontend to backend, eliminate mock data, enable all platform features

---

## 🎯 Executive Summary

### Current State
- **Backend**: 140+ API endpoints, fully functional, running on port 8020
- **Frontend**: 13 pages, only 2 connected to backend (~4% integration)
- **Issue**: Most pages use mock data, 122+ endpoints unused
- **Impact**: Platform appears to work but collects no real data

### Target State (Week 14 End)
- **Backend Integration**: 95%+ of endpoints connected
- **Mock Data**: Zero in production flows
- **Platform**: Fully functional data collection, validation, and MLOps
- **Users**: Can contribute, validate, and manage content in real-time

---

## 📅 Week-by-Week Plan

## WEEK 11: Critical User Flows (HIGH PRIORITY)

### Monday-Tuesday: Submit Page Integration (Task 9.1)

**Objective**: Enable real data collection from users

#### Day 1: Setup & API Client Configuration
```typescript
// File: frontend-main/src/lib/apiClient.ts
Tasks:
1. Create centralized API client
2. Configure base URL: http://localhost:8020/api/v1
3. Add authentication headers (Supabase token → Bearer)
4. Implement error handling and retry logic
5. Add request/response interceptors
6. Set up TypeScript types for all endpoints

Time: 4 hours
```

#### Day 2: Audio Submission
```typescript
// File: frontend-main/src/pages/Submit.tsx
Tasks:
1. Replace mock uploadAudio with real API call
2. Connect to POST /api/v1/submit/audio
3. Implement FormData for file upload
4. Add progress tracking
5. Handle file size validation
6. Add metadata fields (language, dialect, category)
7. Test with real audio file
8. Add success/error notifications

Time: 6 hours
```

#### Day 3: Text & Link Submissions
```typescript
Tasks:
1. Connect text submission to POST /api/v1/submit/text
2. Connect link submission to POST /api/v1/submit/link
3. Add form validation
4. Implement submission history (GET /api/v1/submit/history)
5. Add submission tracking UI
6. Test all submission types
7. Handle edge cases (network errors, large files)

Time: 6 hours
```

**Deliverables**:
- ✅ Users can submit audio, text, and links
- ✅ Submissions stored in MongoDB + Hetzner Storage
- ✅ Submission history visible
- ✅ Error handling and validation working

**Testing Checklist**:
- [ ] Submit 10KB audio file → Success
- [ ] Submit 50MB audio file → Success with progress
- [ ] Submit text (500 chars) → Success
- [ ] Submit external link → Success
- [ ] Check MongoDB for entries
- [ ] Check Hetzner Storage for files
- [ ] Test network failure handling
- [ ] Test authentication failure

---

### Wednesday-Thursday: Validate Page Integration (Task 9.2)

**Objective**: Enable community validation and quality control

#### Day 4: Validation Queue
```typescript
// File: frontend-main/src/pages/Validate.tsx
Tasks:
1. Replace mock validation queue with real API
2. Connect to GET /api/v1/validate/pending
3. Implement queue refresh mechanism
4. Add filters (language, type, tier)
5. Display submission metadata
6. Add pagination
7. Test with multiple submissions

Time: 5 hours
```

#### Day 5: Validation Submission
```typescript
Tasks:
1. Build validation form (quality score 1-10)
2. Connect to POST /api/v1/validate/{submission_id}
3. Add feedback text area
4. Implement consensus display (GET /api/v1/validate/consensus/{id})
5. Show validator statistics (GET /api/v1/validate/stats/validator)
6. Add validation history (GET /api/v1/validate/my-reviews)
7. Test complete validation flow
8. Verify tier promotion logic

Time: 6 hours
```

#### Day 6: Dispute Workflow
```typescript
Tasks:
1. Add dispute button to validations
2. Connect to POST /api/v1/validate/dispute/{validation_id}
3. Implement dispute reason form
4. Add dispute status tracking
5. Test dispute resolution flow

Time: 3 hours
```

**Deliverables**:
- ✅ Validators see real pending submissions
- ✅ Can submit quality scores and feedback
- ✅ Consensus tracking working
- ✅ Tier promotion automated
- ✅ Dispute system functional

**Testing Checklist**:
- [ ] Queue shows real submissions
- [ ] Submit validation → Updates database
- [ ] 3+ validations → Tier promotion
- [ ] Consensus calculation correct
- [ ] Statistics update in real-time
- [ ] Disputes recorded properly

---

### Friday: Community Page Integration (Task 9.3)

**Objective**: Enable real gamification and community engagement

#### Day 7: Leaderboard & Achievements
```typescript
// File: frontend-main/src/pages/Community.tsx
Tasks:
1. Connect leaderboard to GET /api/v1/community/leaderboard
2. Add filters (language family, time period)
3. Display achievements from GET /api/v1/community/achievements
4. Show user achievements (GET /api/v1/community/achievements/user)
5. Implement activity feed (GET /api/v1/community/activity/feed)
6. Add language contributor list
7. Display engagement stats
8. Test point awards system
9. Add real-time updates

Time: 8 hours
```

**Deliverables**:
- ✅ Real leaderboard with actual rankings
- ✅ Achievement system working
- ✅ Activity feed showing contributions
- ✅ Point awards automated

**Testing Checklist**:
- [ ] Leaderboard shows top contributors
- [ ] Points update after submission
- [ ] Achievements unlock correctly
- [ ] Activity feed updates in real-time

---

## WEEK 12: Administration & Strategy (HIGH PRIORITY)

### Monday-Wednesday: Moderation Page Integration (Task 9.4)

**Objective**: Enable content governance and dispute resolution

#### Day 8-9: Moderation Dashboard
```typescript
// File: frontend-main/src/pages/Moderation.tsx
Tasks:
1. Connect to GET /api/v1/governance/moderation/dashboard
2. Display moderation statistics
3. Implement moderation queue
4. Connect actions to POST /api/v1/governance/moderation/actions
5. Add action buttons (approve, reject, flag)
6. Implement dispute management
7. Test moderator permissions

Time: 12 hours
```

#### Day 10: Dispute Resolution
```typescript
Tasks:
1. Display disputes (GET /api/v1/governance/disputes)
2. Add dispute creation form
3. Implement voting (POST /api/v1/governance/disputes/{id}/vote)
4. Show guidelines (GET /api/v1/governance/guidelines)
5. Add report management
6. Test complete moderation workflow

Time: 6 hours
```

**Deliverables**:
- ✅ Moderators can manage content
- ✅ Dispute resolution working
- ✅ Guidelines accessible
- ✅ Reports tracked

---

### Thursday: Authentication Strategy Decision (Task 9.5)

**Objective**: Decide and implement unified auth strategy

#### Day 11: Strategy Planning
```
Meeting: 2 hours
- Review current setup (Supabase frontend, backend auth unused)
- Evaluate 3 options:
  A. Migrate to backend auth (best long-term)
  B. Keep Supabase, sync to backend (easiest)
  C. Hybrid approach (middle ground)
- Make decision
- Document approach
```

#### Day 11-12: Implementation
```typescript
// Assuming Option C (Hybrid - most likely choice)
Tasks:
1. Document authentication flow
2. Update API client with Supabase token
3. Implement token refresh mechanism
4. Add user sync to backend on login
5. Test protected endpoints
6. Implement role-based access
7. Add logout flow
8. Update all API calls with auth headers

Time: 8 hours
```

**Deliverables**:
- ✅ Unified authentication strategy documented
- ✅ All API calls include auth
- ✅ Role-based access working
- ✅ User data synced

---

### Friday: Integration Testing & Bug Fixes

#### Day 13: End-to-End Testing
```
Tasks:
1. Test complete user journey: Register → Submit → Validate
2. Test moderator workflow
3. Verify data persistence
4. Check authorization on all endpoints
5. Performance testing (load times, API response)
6. Fix bugs found during testing
7. Code review and refactoring
8. Update documentation

Time: 8 hours
```

**Week 12 Deliverables**:
- ✅ All critical flows working
- ✅ Authentication unified
- ✅ Moderation functional
- ✅ No blocking bugs

---

## WEEK 13: MLOps Platform (MEDIUM PRIORITY)

### Monday-Wednesday: MLOps Dashboard (Task 9.6)

**Objective**: Make 50+ MLOps endpoints accessible via UI

#### Day 14-15: Models Section
```typescript
// File: frontend-main/src/pages/MLOps.tsx (NEW)
Tasks:
1. Create new MLOps page component
2. Add routing for /mlops
3. Build model grid using GET /api/v1/models
4. Add filters (type, language, version)
5. Implement model detail page
6. Add download interface
7. Connect search (GET /api/v1/models/search)
8. Display statistics (GET /api/v1/models/stats)
9. Test model registration flow

Time: 12 hours
```

#### Day 16: Pipelines Section
```typescript
Tasks:
1. Build pipeline list (GET /api/v1/pipelines)
2. Create stage progress visualization
3. Add metrics dashboard
4. Implement pipeline creation wizard
5. Add artifact browser
6. Test complete pipeline workflow

Time: 8 hours
```

#### Day 17: Resources Section
```typescript
Tasks:
1. Build resource browser (GET /api/v1/resources/links)
2. Add file upload interface
3. Implement verification workflow
4. Add voting system
5. Track clicks and statistics
6. Test resource submission

Time: 6 hours
```

**Deliverables**:
- ✅ MLOps Dashboard live at /mlops
- ✅ Models browsable and downloadable
- ✅ Pipelines tracked with progress
- ✅ Resources manageable

---

### Thursday-Friday: Discovery Features (Task 9.7)

**Objective**: Implement resource recommendations and trending

#### Day 18-19: Discovery Integration
```typescript
// File: frontend-main/src/pages/LanguageDetail.tsx (ENHANCE)
Tasks:
1. Connect to GET /api/v1/discovery/languages/{code}
2. Add all resources view (models/datasets/resources)
3. Implement trending sections
4. Add recommendations (similar models, compatible datasets)
5. Connect global search
6. Add task-based browsing
7. Show overview statistics
8. Test discovery algorithms

Time: 12 hours
```

**Deliverables**:
- ✅ Resource discovery working
- ✅ Recommendations accurate
- ✅ Trending sections populated
- ✅ Search across all resources

---

## WEEK 14: Datasets & Search (LOW PRIORITY)

### Monday-Tuesday: Datasets Page (Task 9.8)

**Objective**: Connect external dataset integrations

#### Day 20-21: Dataset Management
```typescript
// File: frontend-main/src/pages/Datasets.tsx
Tasks:
1. Connect to GET /api/v1/datasets/
2. Display dataset details
3. Show version history
4. Add version comparison tool
5. Implement download interface
6. Show processing jobs
7. Display manifests
8. Test version control workflow

Time: 12 hours
```

**Deliverables**:
- ✅ Datasets browsable
- ✅ Versions tracked
- ✅ Downloads working

---

### Wednesday: Notebooks Management (Task 9.9)

**Objective**: Enable Jupyter notebook sharing

#### Day 22: Notebooks Interface
```typescript
// File: frontend-main/src/components/Notebooks/ (NEW)
Tasks:
1. Create notebooks browser
2. Display featured/trending notebooks
3. Add upload interface
4. Implement notebook detail page
5. Add versioning and comments
6. Connect bookmark/vote features
7. Test publish workflow

Time: 8 hours
```

**Deliverables**:
- ✅ Notebooks shareable
- ✅ Community can discover notebooks

---

### Thursday-Friday: Search Enhancement (Task 9.10)

**Objective**: Powerful cross-platform search

#### Day 23-24: Unified Search
```typescript
// File: frontend-main/src/pages/Search.tsx
Tasks:
1. Connect to multiple search endpoints
2. Build unified search interface
3. Add filters and facets
4. Implement autocomplete
5. Show result counts by category
6. Add recent searches
7. Test search performance

Time: 12 hours
```

**Deliverables**:
- ✅ Search works across all resources
- ✅ Filters functional
- ✅ Performance acceptable

---

## 🛠️ Technical Implementation Guide

### API Client Setup

```typescript
// frontend-main/src/lib/apiClient.ts
import axios from 'axios';
import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8020/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to all requests
apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Example usage
export const submitAudio = async (file: File, metadata: any) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('metadata', JSON.stringify(metadata));

  const response = await apiClient.post('/submit/audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
```

### Error Handling Pattern

```typescript
// frontend-main/src/hooks/useApiCall.ts
import { useState } from 'react';
import { toast } from '@/components/ui/use-toast';

export function useApiCall<T>(apiFunction: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFunction();
      setData(result);
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, execute };
}
```

### TypeScript Types

```typescript
// frontend-main/src/types/api.ts
export interface Submission {
  id: string;
  type: 'audio' | 'text' | 'link';
  language_code: string;
  content?: string;
  file_url?: string;
  tier: 'tier-1-validated' | 'tier-2-reviewed' | 'tier-3-submitted';
  status: 'pending' | 'validated' | 'rejected';
  quality_score?: number;
  created_at: string;
}

export interface ValidationRequest {
  submission_id: string;
  quality_score: number;
  feedback?: string;
  is_culturally_appropriate: boolean;
}

export interface Model {
  model_uuid: string;
  name: string;
  model_type: 'tts' | 'asr' | 'nmt';
  languages: string[];
  version: string;
  performance_metrics?: Record<string, number>;
  download_url?: string;
}
```

---

## 📊 Success Metrics & KPIs

### Weekly Tracking

| Metric | Week 11 | Week 12 | Week 13 | Week 14 | Target |
|--------|---------|---------|---------|---------|---------|
| **Backend endpoints connected** | 30% | 50% | 75% | 95% | 95% |
| **Pages using mock data** | 8 | 4 | 2 | 0 | 0 |
| **CRUD operations tested** | 40% | 70% | 90% | 100% | 100% |
| **API response time (avg)** | - | <200ms | <150ms | <150ms | <200ms |
| **Test coverage** | 50% | 65% | 75% | 80% | 80% |

### User Metrics (After Week 14)

- [ ] 10+ real submissions per day
- [ ] 5+ active validators per week
- [ ] Leaderboard updates real-time
- [ ] <2s page load time
- [ ] 95%+ uptime

---

## 🚨 Risk Management

### High-Risk Items

1. **Authentication Migration**
   - Risk: Breaking existing auth flows
   - Mitigation: Test in staging, gradual rollout
   - Fallback: Keep Supabase as primary

2. **File Upload Performance**
   - Risk: Large files timeout or fail
   - Mitigation: Chunked uploads, progress tracking
   - Fallback: Direct Hetzner upload

3. **Database Connection Issues**
   - Risk: MongoDB connection failures
   - Mitigation: Connection pooling, retry logic
   - Fallback: Graceful degradation to cached data

### Medium-Risk Items

4. **API Response Times**
   - Risk: Slow queries on large datasets
   - Mitigation: Add indexes, implement caching
   - Monitor: APM tools, query profiling

5. **Frontend State Management**
   - Risk: Complex state with multiple API calls
   - Mitigation: Use React Query for caching
   - Tool: Redux DevTools for debugging

---

## ✅ Definition of Done

### Per Task
- [ ] Code implemented and tested
- [ ] Unit tests written (80% coverage)
- [ ] Integration test passes
- [ ] Error handling added
- [ ] Loading states implemented
- [ ] TypeScript types complete
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed to staging

### Per Week
- [ ] All tasks completed
- [ ] End-to-end test passes
- [ ] Performance metrics met
- [ ] No blocking bugs
- [ ] Documentation updated
- [ ] Demo to stakeholders

### Project Complete (End of Week 14)
- [ ] 95%+ backend endpoints connected
- [ ] Zero mock data in production
- [ ] All CRUD operations tested
- [ ] Full error handling
- [ ] Loading states everywhere
- [ ] 80%+ test coverage
- [ ] API client properly typed
- [ ] All pages functional
- [ ] Production deployment successful
- [ ] User acceptance testing passed

---

## 📚 Resources

### Documentation
- Backend API: `http://localhost:8020/docs`
- API Mapping: `/opt/kasaai/apps/community/FRONTEND_BACKEND_API_MAPPING.md`
- Task List: `/opt/kasaai/apps/community/TASK.md`

### Code Locations
- Backend: `/opt/kasaai/apps/community/backend/`
- Frontend: `/opt/kasaai/apps/community/frontend-main/`
- API Client: `frontend-main/src/lib/api.ts`
- Pages: `frontend-main/src/pages/`

### Tools
- API Testing: Postman, curl
- State Management: React Query
- Form Handling: React Hook Form
- UI Components: shadcn/ui
- Testing: Vitest, React Testing Library

---

## 🎯 Next Steps

### Immediate (Today)
1. Review this plan with team
2. Set up development environment
3. Test all backend endpoints with Postman
4. Create feature branch: `feature/frontend-backend-integration`

### Week 11 Day 1 (Tomorrow)
1. Create API client configuration
2. Set up TypeScript types
3. Begin Submit page integration
4. Daily standup at 9 AM

### Ongoing
- Daily standups (15 min)
- Code reviews (within 24 hours)
- Weekly demos (Friday 3 PM)
- Documentation updates (continuous)

---

**Owner**: Development Team
**Reviewer**: Tech Lead
**Stakeholders**: Product Manager, QA Team
**Timeline**: November 2025 (Weeks 11-14)
**Status**: Ready to Start ✅
