# StudyFlow - Complete JIRA Breakdown
**Version:** 1.0
**Date:** 2025-11-07
**Status:** Ready for Import

---

## Executive Summary

This document provides a complete breakdown of epics, stories, and tasks for StudyFlow to reach production-ready status. Based on thorough codebase analysis:

**Current Status:**
- Backend: 85% complete (67 endpoints, 10 services, 7 models)
- Frontend Admin Portal: 40% complete (15 pages, 7 API modules)
- Mobile App (Student Interface): 0% complete
- Parent Portal: 0% complete
- Exercise System: 0% complete
- Test Coverage: ~10-15%

**Total Work Remaining:** 13 Epics, 62 Stories, 187 Tasks

---

## EPIC BREAKDOWN

### Epic 1: Testing & Quality Assurance (CRITICAL - MUST DO FIRST)
**Priority:** P0 - Critical
**Status:** Not Started
**Completion:** 10%
**Target Date:** Week 1-3

**Business Value:** Ensure system reliability, prevent regressions, enable confident deployments

#### User Stories

##### Story 1.1: Backend Unit Test Coverage
**Story Points:** 13
**Priority:** P0
**Acceptance Criteria:**
- Achieve 80%+ code coverage on backend
- All services have comprehensive unit tests
- All models have validation tests
- Edge cases and error scenarios covered

**Tasks:**
1. **[TASK-001]** Setup pytest coverage tracking and reporting (2 hours)
   - Install pytest-cov
   - Configure coverage.py
   - Add coverage report to CI/CD
   - Set 80% minimum threshold

2. **[TASK-002]** Write unit tests for auth service (8 hours)
   - Test user registration flow
   - Test multi-role authentication
   - Test parent-student linking
   - Test JWT token management
   - Test role-based access control
   - Expected: 15+ test cases

3. **[TASK-003]** Write unit tests for materials service (12 hours)
   - Test file upload validation
   - Test metadata tagging
   - Test CRUD operations
   - Test permission checks
   - Test file type validation
   - Expected: 20+ test cases

4. **[TASK-004]** Write unit tests for tutoring service (16 hours)
   - Test session creation/management
   - Test RAG query integration
   - Test cost calculation
   - Test conversation history tracking
   - Test confidence scoring
   - Mock RAG service responses
   - Expected: 25+ test cases

5. **[TASK-005]** Write unit tests for school service (8 hours)
   - Test school CRUD operations
   - Test subscription tier limits
   - Test statistics aggregation
   - Test organization scoping
   - Expected: 15+ test cases

6. **[TASK-006]** Write unit tests for user service (6 hours)
   - Test user profile management
   - Test role transitions
   - Test data validation
   - Expected: 12+ test cases

7. **[TASK-007]** Write unit tests for analytics service (8 hours)
   - Test dashboard statistics
   - Test metric aggregations
   - Test date range filtering
   - Expected: 15+ test cases

8. **[TASK-008]** Expand existing progress and wallet tests (4 hours)
   - Add edge case coverage
   - Test concurrent operations
   - Test transaction rollback scenarios

---

##### Story 1.2: Backend Integration Tests
**Story Points:** 8
**Priority:** P0
**Acceptance Criteria:**
- Complete user flows tested end-to-end
- Database operations tested with real MongoDB
- External service integrations tested (mocked)

**Tasks:**
1. **[TASK-009]** Setup integration test environment (4 hours)
   - Configure test MongoDB instance
   - Create test data fixtures
   - Setup test isolation between runs

2. **[TASK-010]** Integration test: Upload-to-RAG pipeline (6 hours)
   - Test: Upload PDF → Process → Embed → Query
   - Verify chunks created correctly
   - Verify embeddings stored
   - Test semantic search accuracy

3. **[TASK-011]** Integration test: Complete tutoring flow (8 hours)
   - Test: Create session → Ask questions → Deduct wallet → Track progress
   - Verify all side effects (wallet deduction, progress update)
   - Test multi-question conversations
   - Expected: 10+ test scenarios

4. **[TASK-012]** Integration test: Payment workflow (6 hours)
   - Test: Top-up → Webhook → Credit wallet → Verify balance
   - Mock Paystack/MoMo webhooks
   - Test idempotency
   - Test refund scenarios

5. **[TASK-013]** Integration test: Parent-student relationships (4 hours)
   - Test parent viewing student progress
   - Test permission boundaries
   - Test data aggregation for multiple students

---

##### Story 1.3: Frontend Testing Infrastructure
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Vitest or Jest configured
- Critical user flows have E2E tests
- API client has comprehensive tests

**Tasks:**
1. **[TASK-014]** Setup Vitest testing framework (3 hours)
   - Install and configure Vitest
   - Setup testing-library/react
   - Configure test environment
   - Add npm test scripts

2. **[TASK-015]** Write tests for API client (8 hours)
   - Test all 7 service modules
   - Test error handling
   - Test authentication header injection
   - Mock fetch responses
   - Expected: 30+ test cases

3. **[TASK-016]** Write component tests for critical UI (6 hours)
   - Test MaterialUpload component
   - Test Wallet component
   - Test AdminDashboard
   - Test form validation

4. **[TASK-017]** Setup E2E testing with Playwright (4 hours)
   - Install Playwright
   - Configure test environment
   - Write E2E test for login flow
   - Write E2E test for material upload flow

---

##### Story 1.4: CI/CD Pipeline Setup
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Automated testing on every PR
- Test results block merges if failing
- Coverage reports generated
- Deployment automation configured

**Tasks:**
1. **[TASK-018]** Setup GitHub Actions CI workflow (4 hours)
   - Create workflow file
   - Run backend tests on PR
   - Run frontend tests on PR
   - Generate coverage reports
   - Block merge if tests fail

2. **[TASK-019]** Setup deployment automation (4 hours)
   - Automate backend deployment to dev server
   - Automate frontend build and deployment
   - Add staging environment checks

3. **[TASK-020]** Configure test result notifications (2 hours)
   - Slack notifications for test failures
   - Email alerts for critical issues

---

### Epic 2: RAG Material Processing Pipeline (CRITICAL)
**Priority:** P0 - Critical
**Status:** Partially Complete (30%)
**Completion:** 30%
**Target Date:** Week 2-3

**Business Value:** Enable AI tutoring by making study materials searchable and queryable

#### User Stories

##### Story 2.1: Complete Material-to-RAG Pipeline
**Story Points:** 8
**Priority:** P0
**Acceptance Criteria:**
- Materials automatically processed on upload
- Chunks extracted intelligently
- Embeddings created and stored
- Semantic search returns relevant results

**Tasks:**
1. **[TASK-021]** Fix DocumentProcessor integration in material upload (6 hours)
   - Connect upload endpoint to DocumentProcessor
   - Configure chunking strategy (sentence-aware, 800 chars)
   - Store chunks in material metadata
   - Handle processing errors gracefully

2. **[TASK-022]** Implement RAG embedding workflow (8 hours)
   - After document processing, trigger embedding
   - Create collection per school+subject: `school_{id}_{subject}`
   - Store embeddings in pgvector
   - Track embedding status in material model
   - Update material status to "completed" when done

3. **[TASK-023]** Implement background processing with Celery/RQ (12 hours)
   - Setup task queue (Redis + Celery or RQ)
   - Move document processing to background tasks
   - Add progress tracking for long files
   - Implement retry logic for failures
   - Send notifications on completion/failure

4. **[TASK-024]** Add re-indexing capability (4 hours)
   - API endpoint to re-process material
   - Delete old embeddings before re-indexing
   - Bulk re-index for all materials in subject

5. **[TASK-025]** Test RAG answer quality (8 hours)
   - Upload 10 sample textbooks
   - Ask 50 test questions
   - Measure answer accuracy (target >85%)
   - Identify and fix common failure modes
   - Document best practices for material uploads

---

##### Story 2.2: Knowledge Base Management
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Admins can view embedding statistics
- Collections can be rebuilt if corrupted
- Orphaned embeddings can be cleaned up

**Tasks:**
1. **[TASK-026]** Add knowledge base statistics endpoint (4 hours)
   - Endpoint: GET /api/v1/materials/kb-stats
   - Show total embeddings per collection
   - Show collection sizes
   - Show last updated timestamps

2. **[TASK-027]** Add collection rebuild functionality (6 hours)
   - Admin endpoint to rebuild collection
   - Delete all embeddings in collection
   - Re-process all materials for that subject
   - Track rebuild progress

3. **[TASK-028]** Implement embedding cleanup job (4 hours)
   - Find orphaned embeddings (no matching material)
   - Delete old embeddings after material deletion
   - Schedule cleanup job weekly

---

### Epic 3: Mobile App - Student Interface (CRITICAL)
**Priority:** P0 - Critical
**Status:** Not Started
**Completion:** 0%
**Target Date:** Week 3-8

**Business Value:** Primary interface for students to learn, ask questions, and practice

#### User Stories

##### Story 3.1: Mobile App Foundation
**Story Points:** 8
**Priority:** P0
**Acceptance Criteria:**
- React Native/Expo project initialized
- Navigation configured
- Authentication working
- API client integrated

**Tasks:**
1. **[TASK-029]** Initialize Expo project with TypeScript (4 hours)
   - Run `expo init` with TypeScript template
   - Configure project structure
   - Setup linting and formatting
   - Install core dependencies

2. **[TASK-030]** Setup React Navigation (4 hours)
   - Install navigation packages
   - Configure stack and tab navigators
   - Create navigation types
   - Setup deep linking

3. **[TASK-031]** Configure authentication with Supabase (6 hours)
   - Install Supabase client
   - Create auth context
   - Implement secure token storage
   - Add auto-refresh logic

4. **[TASK-032]** Create reusable API client (6 hours)
   - Port API client from web app
   - Add request/response interceptors
   - Handle authentication headers
   - Add error handling

5. **[TASK-033]** Setup state management (4 hours)
   - Install and configure React Query
   - Create query hooks for common operations
   - Setup cache invalidation strategies

---

##### Story 3.2: Authentication Screens
**Story Points:** 5
**Priority:** P0
**Acceptance Criteria:**
- Students can log in with email/password
- Registration flow works
- Password reset implemented
- Elegant error handling

**Tasks:**
1. **[TASK-034]** Design and implement Splash screen (3 hours)
   - Animated logo
   - App name and tagline
   - Auto-navigate after 2s

2. **[TASK-035]** Design and implement Login screen (4 hours)
   - Email/password form
   - "Remember me" checkbox
   - "Forgot password" link
   - Error messages
   - Loading state

3. **[TASK-036]** Design and implement Registration screen (6 hours)
   - Multi-step form (email, password, profile)
   - Grade selection
   - School selection
   - Parent link code (optional)
   - Validation

4. **[TASK-037]** Implement password reset flow (3 hours)
   - Forgot password screen
   - OTP verification (if needed)
   - Reset password screen

---

##### Story 3.3: Home & Subject Navigation
**Story Points:** 5
**Priority:** P0
**Acceptance Criteria:**
- Students see their subjects
- Daily stats displayed
- Continue learning functionality
- Subject details screen works

**Tasks:**
1. **[TASK-038]** Design and implement Home screen (8 hours)
   - Welcome message with student name
   - Today's learning stats (time, questions, streak)
   - Subject grid/list
   - "Continue learning" card
   - Achievement badges (if any)
   - Bottom tab navigation

2. **[TASK-039]** Design and implement Subject List screen (4 hours)
   - Display subjects from materials
   - Subject cards with icons
   - Progress indicators
   - Recent activity

3. **[TASK-040]** Design and implement Subject Details screen (6 hours)
   - Show topics for selected subject
   - Topic list with mastery levels
   - "Ask Question" button
   - "Take Exercise" button
   - Progress chart for this subject

---

##### Story 3.4: AI Tutoring Interface (Q&A)
**Story Points:** 13
**Priority:** P0
**Acceptance Criteria:**
- Students can type questions
- AI answers displayed clearly
- Source citations shown
- Conversation history tracked
- Cost per question visible

**Tasks:**
1. **[TASK-041]** Design and implement Tutoring Session screen (12 hours)
   - Chat-style interface
   - Message bubbles (student vs AI)
   - Text input with send button
   - Typing indicator while loading
   - Question counter
   - Session timer
   - Cost tracker

2. **[TASK-042]** Implement question submission flow (6 hours)
   - Create session on first question
   - Send question to backend
   - Display loading state
   - Handle errors gracefully
   - Update session cost

3. **[TASK-043]** Implement answer display with sources (6 hours)
   - Format AI answer with markdown
   - Show confidence score
   - Display source citations (material + page)
   - "Explain simpler" button
   - "Related topics" suggestions

4. **[TASK-044]** Implement conversation history (4 hours)
   - Save conversation locally
   - Display past questions in session
   - Scroll to latest message
   - Export conversation feature

5. **[TASK-045]** Add "Explain Simpler" feature (4 hours)
   - Button on each AI answer
   - Re-query RAG with "explain like I'm {grade-2}"
   - Show simplified answer
   - Track additional cost

---

##### Story 3.5: Voice Input (Optional Phase 2)
**Story Points:** 8
**Priority:** P2
**Acceptance Criteria:**
- Students can speak questions
- Speech-to-text accurate
- Answers can be read aloud
- Works in English (Twi/French later)

**Tasks:**
1. **[TASK-046]** Integrate Speech-to-Text (Whisper) (8 hours)
   - Add microphone permission
   - Record audio
   - Send to Whisper API
   - Display transcribed text
   - Allow editing before sending

2. **[TASK-047]** Integrate Text-to-Speech (Voice Lab) (6 hours)
   - Add speaker button on answers
   - Fetch TTS audio from backend
   - Play audio in app
   - Pause/resume controls

---

##### Story 3.6: Progress & Profile Screens
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Students see their progress
- Subject breakdown visible
- Learning streak displayed
- Profile can be edited

**Tasks:**
1. **[TASK-048]** Design and implement Progress screen (8 hours)
   - Overall stats card (sessions, questions, time)
   - Subject breakdown with charts
   - Topic mastery heatmap
   - Learning streak calendar
   - Recent activity list

2. **[TASK-049]** Design and implement Profile screen (4 hours)
   - Profile picture (optional upload)
   - Name, email, grade
   - Edit profile form
   - Logout button
   - App version and support links

3. **[TASK-050]** Add learning streak tracking (4 hours)
   - Visual streak calendar
   - Streak count badge
   - Motivation messages
   - Push notification reminder if streak at risk

---

### Epic 4: Exercise System (HIGH PRIORITY)
**Priority:** P1 - High
**Status:** Not Started
**Completion:** 0%
**Target Date:** Week 5-8

**Business Value:** Practice reinforces learning, provides assessment data

#### User Stories

##### Story 4.1: Exercise Generation Backend
**Story Points:** 8
**Priority:** P1
**Acceptance Criteria:**
- API generates MCQs from study materials
- Questions match topic and difficulty
- Questions include explanations
- Adaptive difficulty based on performance

**Tasks:**
1. **[TASK-051]** Create exercise model and schema (3 hours)
   - Exercise model with questions
   - Question model (MCQ, short answer, essay)
   - Metadata (topic, difficulty, correct answer)
   - Student submission tracking

2. **[TASK-052]** Implement exercise generation service (12 hours)
   - Use RAG to generate questions from materials
   - Parse AI response into structured questions
   - Validate question format
   - Store exercise in MongoDB
   - Track generation cost

3. **[TASK-053]** Create exercise generation API endpoints (4 hours)
   - POST /api/v1/exercises/generate
   - GET /api/v1/exercises (list available)
   - GET /api/v1/exercises/{id} (get exercise)

4. **[TASK-054]** Implement adaptive difficulty logic (4 hours)
   - Analyze student's past performance
   - Increase difficulty if score >80%
   - Decrease difficulty if score <60%
   - Recommend exercises based on weak areas

---

##### Story 4.2: Exercise Submission & Grading
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Students can submit answers
- Auto-grading for MCQs
- Instant feedback with explanations
- Score tracked in progress

**Tasks:**
1. **[TASK-055]** Implement exercise submission API (4 hours)
   - POST /api/v1/exercises/{id}/submit
   - Validate submission format
   - Calculate score
   - Update student progress

2. **[TASK-056]** Implement auto-grading service (6 hours)
   - Grade MCQs automatically
   - Use AI to grade short answers (with rubric)
   - Generate feedback for incorrect answers
   - Calculate total score

3. **[TASK-057]** Create feedback response (4 hours)
   - Per-question feedback
   - Correct answer + explanation
   - Performance summary
   - Recommendations for improvement

---

##### Story 4.3: Exercise UI (Mobile)
**Story Points:** 8
**Priority:** P1
**Acceptance Criteria:**
- Students can browse exercises
- Take exercises with timer
- See results with feedback
- Review past exercises

**Tasks:**
1. **[TASK-058]** Design and implement Exercise List screen (6 hours)
   - List exercises by subject/topic
   - Show difficulty and length
   - Completed vs available badges
   - Scores for completed exercises

2. **[TASK-059]** Design and implement Take Exercise screen (12 hours)
   - Question display (1 at a time or all)
   - MCQ option selection
   - Timer display (optional countdown)
   - Progress indicator (3/10)
   - Submit button
   - Confirmation before submit

3. **[TASK-060]** Design and implement Exercise Results screen (8 hours)
   - Score display with animation
   - Performance summary
   - Per-question review
   - Correct vs incorrect indicators
   - Explanations
   - "Retry" and "Back" buttons

4. **[TASK-061]** Implement exercise history (3 hours)
   - List past exercises
   - Show scores and dates
   - Allow viewing results again

---

### Epic 5: Parent Dashboard (HIGH PRIORITY)
**Priority:** P1 - High
**Status:** Not Started
**Completion:** 0%
**Target Date:** Week 6-9

**Business Value:** Parents need visibility to trust and pay for the service

#### User Stories

##### Story 5.1: Parent Dashboard Backend
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- API aggregates data for all linked students
- Weekly summaries calculated
- Performance comparisons available

**Tasks:**
1. **[TASK-062]** Create parent dashboard API endpoint (6 hours)
   - GET /api/v1/parents/dashboard
   - Aggregate data for all linked students
   - Calculate weekly summaries
   - Identify weak areas across students

2. **[TASK-063]** Implement multi-student comparison (4 hours)
   - Compare performance between siblings
   - Identify which child needs more support
   - Show relative progress

---

##### Story 5.2: Parent Web Portal UI
**Story Points:** 13
**Priority:** P1
**Acceptance Criteria:**
- Parents can log in
- See all linked students
- View individual student details
- Manage wallet and spending

**Tasks:**
1. **[TASK-064]** Create parent portal project structure (3 hours)
   - Separate Next.js project or route in existing
   - Configure parent-specific routes
   - Setup authentication for parents

2. **[TASK-065]** Design and implement Parent Dashboard (12 hours)
   - Overview of all linked students
   - Key stats per student (time, sessions, score)
   - Wallet balance with top-up button
   - This week's spending
   - Quick actions (top-up, view reports)

3. **[TASK-066]** Design and implement Student Detail view (8 hours)
   - Individual student page
   - Learning activity chart
   - Subject breakdown
   - Weak areas identification
   - Recent questions asked
   - Exercise performance

4. **[TASK-067]** Implement spending controls (6 hours)
   - Set daily spending limit
   - Set weekly spending limit
   - Low balance threshold setting
   - Notification preferences

5. **[TASK-068]** Add student linking interface (4 hours)
   - Parent can link new students
   - Generate link code for student to enter
   - Unlink student (with confirmation)

---

### Epic 6: AI-Generated Weekly Reports
**Priority:** P1 - High
**Status:** Not Started
**Completion:** 0%
**Target Date:** Week 7-10

**Business Value:** Automated insights build trust and keep parents engaged

#### User Stories

##### Story 6.1: Report Generation Service
**Story Points:** 8
**Priority:** P1
**Acceptance Criteria:**
- Reports generated every Sunday
- AI analyzes performance and generates insights
- Reports include actionable recommendations
- Parents receive via email/WhatsApp

**Tasks:**
1. **[TASK-069]** Create report generation service (12 hours)
   - Aggregate weekly data per student
   - Calculate statistics (time, questions, scores, subjects)
   - Use RAG to generate AI summary
   - Identify strengths and weak areas
   - Generate recommendations
   - Store report in MongoDB

2. **[TASK-070]** Design report template (4 hours)
   - HTML email template
   - PDF export template
   - Include charts and visuals
   - Professional layout

3. **[TASK-071]** Implement scheduled report generation (4 hours)
   - Cron job or n8n workflow
   - Trigger every Sunday 6pm
   - Generate for all active students
   - Handle failures gracefully

---

##### Story 6.2: Report Delivery
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Reports emailed to parents
- Reports sent via WhatsApp (optional)
- Reports viewable in parent portal
- Reports downloadable as PDF

**Tasks:**
1. **[TASK-072]** Setup email delivery (SendGrid) (4 hours)
   - Configure SendGrid API
   - Create email template
   - Send test emails
   - Handle bounces and failures

2. **[TASK-073]** Setup WhatsApp delivery via n8n (4 hours)
   - Create n8n workflow
   - Trigger workflow on report generation
   - Send formatted message with link
   - Track delivery status

3. **[TASK-074]** Add reports page to parent portal (6 hours)
   - List past reports
   - View report details
   - Download as PDF
   - Share report (email, link)

---

### Epic 7: Wallet & Payment Integration (HIGH PRIORITY)
**Priority:** P1 - High
**Status:** Backend Complete (100%), Frontend Partial (60%)
**Completion:** 80%
**Target Date:** Week 4-5

**Business Value:** Revenue generation depends on seamless payments

#### User Stories

##### Story 7.1: Paystack Integration
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Parents can top up via Paystack
- Webhook updates wallet balance
- Transaction history tracked
- Refunds supported

**Tasks:**
1. **[TASK-075]** Connect frontend Wallet page to real Paystack (6 hours)
   - Remove mock data
   - Integrate Paystack popup
   - Handle payment success/failure
   - Update UI with real balance

2. **[TASK-076]** Test end-to-end payment flow (4 hours)
   - Test with Paystack test cards
   - Verify webhook updates wallet
   - Test idempotency (duplicate webhooks)
   - Test payment failure scenarios

3. **[TASK-077]** Add refund functionality (4 hours)
   - Refund request form
   - Admin approval workflow
   - Paystack refund API integration
   - Update wallet balance

---

##### Story 7.2: Mobile Money Integration
**Story Points:** 8
**Priority:** P1
**Acceptance Criteria:**
- Parents can top up via MTN/Vodafone/AirtelTigo MoMo
- USSD prompts work correctly
- Webhook confirms payment
- Transaction history updated

**Tasks:**
1. **[TASK-078]** Research and select MoMo payment provider (4 hours)
   - Evaluate providers (Hubtel, Paystack MoMo, direct)
   - Compare fees and ease of integration
   - Setup test account

2. **[TASK-079]** Implement MoMo payment initiation (8 hours)
   - Add MoMo option to top-up modal
   - Initiate payment via API
   - Display USSD prompt to user
   - Poll for payment status

3. **[TASK-080]** Implement MoMo webhook handler (4 hours)
   - Verify webhook signature
   - Update wallet balance
   - Send confirmation notification
   - Handle timeouts and failures

4. **[TASK-081]** Test MoMo integration end-to-end (4 hours)
   - Test with real MoMo accounts
   - Test all networks (MTN, Vodafone, AirtelTigo)
   - Verify balance updates
   - Test edge cases

---

##### Story 7.3: Spending Limits & Alerts
**Story Points:** 3
**Priority:** P2
**Acceptance Criteria:**
- Parents can set daily/weekly limits
- System blocks transactions exceeding limits
- Low balance alerts sent

**Tasks:**
1. **[TASK-082]** Implement spending limit logic (4 hours)
   - Check limit before wallet deduction
   - Block transaction if limit exceeded
   - Send notification to parent

2. **[TASK-083]** Add spending limit UI (3 hours)
   - Settings page for limits
   - Toggle to enable/disable
   - Default limits

3. **[TASK-084]** Implement low balance alerts (3 hours)
   - Check balance after every deduction
   - Send SMS/email if below ₵5
   - Add in-app notification

---

### Epic 8: n8n Workflow Automation
**Priority:** P2 - Medium
**Status:** Partially Complete (20%)
**Completion:** 20%
**Target Date:** Week 8-9

**Business Value:** Automation reduces manual work and improves user engagement

#### User Stories

##### Story 8.1: Core Automation Workflows
**Story Points:** 5
**Priority:** P2
**Acceptance Criteria:**
- Weekly reports automated
- Low balance alerts automated
- Daily reminders sent
- Payment confirmations sent

**Tasks:**
1. **[TASK-085]** Create n8n workflow: Weekly Reports (3 hours)
   - Trigger every Sunday 6pm
   - Fetch all active students
   - Generate reports via API
   - Send emails and WhatsApp messages

2. **[TASK-086]** Create n8n workflow: Low Balance Alerts (2 hours)
   - Webhook trigger on balance check
   - Filter for balance < ₵5
   - Send SMS and email alert
   - Log notification

3. **[TASK-087]** Create n8n workflow: Daily Learning Reminders (3 hours)
   - Trigger daily at parent-set time
   - Send push notification to student
   - Track reminder sent

4. **[TASK-088]** Create n8n workflow: Payment Confirmations (2 hours)
   - Webhook trigger on successful payment
   - Send confirmation email with receipt
   - Send SMS confirmation

---

##### Story 8.2: Re-engagement Workflows
**Story Points:** 3
**Priority:** P3
**Acceptance Criteria:**
- Inactive students get reminders
- Celebrate milestones
- Birthday messages

**Tasks:**
1. **[TASK-089]** Create workflow: Re-engagement Campaign (4 hours)
   - Find students inactive for 7 days
   - Send "We miss you" message
   - Offer incentive (free 10 questions)

2. **[TASK-090]** Create workflow: Milestone Celebrations (3 hours)
   - Trigger on achievements (100 questions, 30-day streak)
   - Send congratulations message
   - Offer badge or reward

3. **[TASK-091]** Create workflow: Birthday Messages (2 hours)
   - Trigger on student birthday
   - Send personalized message
   - Offer birthday bonus credits

---

### Epic 9: Security & Compliance
**Priority:** P1 - High
**Status:** Partially Complete (60%)
**Completion:** 60%
**Target Date:** Week 5-6

**Business Value:** Protect student data, comply with regulations, build trust

#### User Stories

##### Story 9.1: Security Hardening
**Story Points:** 5
**Priority:** P1
**Acceptance Criteria:**
- Parent-student ownership checks enforced
- Rate limiting implemented
- Data encryption at rest
- Audit logs for sensitive operations

**Tasks:**
1. **[TASK-092]** Fix parent-student relationship checks (3 hours)
   - Complete all TODOs in tutoring.py
   - Verify parent owns student before showing data
   - Verify student owns session before accessing
   - Add unit tests

2. **[TASK-093]** Implement rate limiting (4 hours)
   - Add rate limiter middleware
   - Limit Q&A endpoint (10/min per student)
   - Limit payment endpoint (5/hour per parent)
   - Return 429 status with retry-after header

3. **[TASK-094]** Add audit logging (6 hours)
   - Log wallet transactions
   - Log material uploads/deletions
   - Log user role changes
   - Log payment events
   - Store in separate audit collection

4. **[TASK-095]** Implement data encryption (4 hours)
   - Encrypt student names in database
   - Encrypt phone numbers
   - Encrypt email addresses
   - Use envelope encryption with KMS

---

##### Story 9.2: COPPA & GDPR Compliance
**Story Points:** 5
**Priority:** P2
**Acceptance Criteria:**
- Parent consent required for students <13
- Data export available on request
- Data deletion available on request
- Privacy policy and terms integrated

**Tasks:**
1. **[TASK-096]** Implement parental consent flow (4 hours)
   - Check student age on registration
   - Require parent email verification if <13
   - Store consent record
   - Block access until consent obtained

2. **[TASK-097]** Implement data export (4 hours)
   - Endpoint: GET /api/v1/users/export-data
   - Export all user data as JSON
   - Include sessions, questions, progress
   - Zip and send via email

3. **[TASK-098]** Implement data deletion (4 hours)
   - Endpoint: POST /api/v1/users/delete-account
   - Soft delete user account
   - Anonymize personal data
   - Retain aggregated stats (anonymized)
   - Send confirmation email

4. **[TASK-099]** Add privacy policy and terms (3 hours)
   - Create privacy policy page
   - Create terms of service page
   - Require acceptance on registration
   - Log acceptance in database

---

### Epic 10: Voice Tutoring (VAPI Integration) - OPTIONAL
**Priority:** P3 - Low (Post-MVP)
**Status:** Not Started
**Completion:** 0%
**Target Date:** Phase 4

**Business Value:** Enhanced user experience, especially for younger students

#### User Stories

##### Story 10.1: VAPI Integration
**Story Points:** 13
**Priority:** P3
**Acceptance Criteria:**
- Students can have voice conversations with AI tutor
- Function calling integrated (answer questions, generate exercises)
- Voice calls tracked and billed
- Call quality acceptable

**Tasks:**
1. **[TASK-100]** Integrate VAPI service from shared library (4 hours)
   - Test VAPI service from `@shared/integration/vapi.py`
   - Create VAPI assistant for tutoring
   - Configure voice (warm, encouraging tone)
   - Setup webhook endpoint

2. **[TASK-101]** Implement function calling (8 hours)
   - Function: answer_from_knowledge_base
   - Function: give_exercise
   - Function: evaluate_answer
   - Test function calling accuracy

3. **[TASK-102]** Create voice tutoring UI (mobile) (12 hours)
   - Voice call interface
   - Animated speaking indicator
   - Mute/unmute button
   - End call button
   - Call timer and cost tracker

4. **[TASK-103]** Test voice call quality (4 hours)
   - Test with students of different ages
   - Measure voice clarity
   - Test latency
   - Identify and fix issues

---

### Epic 11: Multi-Language Support
**Priority:** P3 - Low (Post-MVP)
**Status:** Not Started
**Completion:** 0%
**Target Date:** Phase 4

**Business Value:** Expand market to non-English speakers, increase accessibility

#### User Stories

##### Story 11.1: App Internationalization (i18n)
**Story Points:** 8
**Priority:** P3
**Acceptance Criteria:**
- App supports English, Twi, French
- Language switchable in settings
- All UI strings translated
- Voice support for all languages

**Tasks:**
1. **[TASK-104]** Setup i18n framework (4 hours)
   - Install react-i18next (mobile) and next-intl (web)
   - Configure translation files
   - Extract all UI strings
   - Create translation keys

2. **[TASK-105]** Translate to Twi (12 hours)
   - Translate all UI strings
   - Translate system prompts
   - Test translations with native speakers
   - Fix issues

3. **[TASK-106]** Translate to French (12 hours)
   - Translate all UI strings
   - Translate system prompts
   - Test translations with native speakers
   - Fix issues

4. **[TASK-107]** Add language selection UI (3 hours)
   - Language picker in settings
   - Show current language
   - Restart app after language change

---

### Epic 12: Offline Mode
**Priority:** P3 - Low (Post-MVP)
**Status:** Not Started
**Completion:** 0%
**Target Date:** Phase 4

**Business Value:** Enable learning in areas with poor connectivity

#### User Stories

##### Story 12.1: Offline Material Access
**Story Points:** 8
**Priority:** P3
**Acceptance Criteria:**
- Students can download materials for offline viewing
- Downloaded materials readable without internet
- Sync progress when back online

**Tasks:**
1. **[TASK-108]** Implement material download (8 hours)
   - Download button on each material
   - Store file in local storage
   - Track download status
   - Show downloaded badge

2. **[TASK-109]** Implement offline viewer (6 hours)
   - PDF viewer that works offline
   - Text viewer for notes
   - Search within downloaded materials

3. **[TASK-110]** Implement offline sync (8 hours)
   - Queue questions asked offline
   - Queue exercise submissions
   - Sync when internet available
   - Show sync status

---

### Epic 13: Admin Tools & Monitoring
**Priority:** P2 - Medium
**Status:** Partially Complete (50%)
**Completion:** 50%
**Target Date:** Week 6-7

**Business Value:** Ops team needs tools to manage and monitor the platform

#### User Stories

##### Story 13.1: Admin Monitoring Dashboard
**Story Points:** 5
**Priority:** P2
**Acceptance Criteria:**
- System health metrics visible
- User activity tracked
- API performance monitored
- Errors logged and alerted

**Tasks:**
1. **[TASK-111]** Enhance system health endpoint (3 hours)
   - Add database connection checks
   - Add RAG service health check
   - Add payment gateway health check
   - Add queue health check

2. **[TASK-112]** Implement structured logging (4 hours)
   - Use JSON logging format
   - Add correlation IDs to requests
   - Log all API calls with duration
   - Log errors with stack traces

3. **[TASK-113]** Setup error tracking (Sentry) (3 hours)
   - Install Sentry SDK
   - Configure error reporting
   - Add user context to errors
   - Setup alert rules

4. **[TASK-114]** Create metrics dashboard (Grafana) (8 hours)
   - Setup Grafana instance
   - Create dashboard for API metrics
   - Add charts for user activity
   - Add alerts for anomalies

---

##### Story 13.2: Content Moderation Tools
**Story Points:** 5
**Priority:** P2
**Acceptance Criteria:**
- Admins can flag inappropriate content
- Low-confidence answers reviewed
- Students can report issues

**Tasks:**
1. **[TASK-115]** Add content flagging system (4 hours)
   - Flag button on questions/answers
   - Store flags in database
   - Admin review queue

2. **[TASK-116]** Auto-flag low-confidence answers (3 hours)
   - Flag answers with confidence <50%
   - Add to review queue
   - Send daily digest to teachers

3. **[TASK-117]** Student issue reporting (3 hours)
   - Report button in app
   - Issue submission form
   - Store in support database
   - Email notification to support team

---

##### Story 13.3: Analytics & Business Intelligence
**Story Points:** 5
**Priority:** P2
**Acceptance Criteria:**
- Revenue metrics tracked
- User retention measured
- Churn analysis available
- Cohort analysis implemented

**Tasks:**
1. **[TASK-118]** Implement revenue analytics (4 hours)
   - Endpoint for daily/weekly/monthly revenue
   - Revenue per student
   - Revenue per school
   - Payment method breakdown

2. **[TASK-119]** Implement retention metrics (4 hours)
   - DAU/MAU calculation
   - Week-over-week retention
   - Cohort retention analysis

3. **[TASK-120]** Implement churn analysis (4 hours)
   - Identify churned users (inactive 30+ days)
   - Churn rate calculation
   - Churn reasons (low balance, poor experience, etc.)

---

## PRIORITY SUMMARY

### P0 - Critical (Must Complete First)
**Target:** Weeks 1-4
**Total Stories:** 15
**Total Tasks:** 60

1. **Epic 1: Testing & Quality Assurance**
   - Story 1.1: Backend Unit Test Coverage (13 SP)
   - Story 1.2: Backend Integration Tests (8 SP)
   - Story 1.3: Frontend Testing Infrastructure (5 SP)
   - Story 1.4: CI/CD Pipeline Setup (5 SP)

2. **Epic 2: RAG Material Processing**
   - Story 2.1: Complete Material-to-RAG Pipeline (8 SP)
   - Story 2.2: Knowledge Base Management (5 SP)

3. **Epic 3: Mobile App Foundation**
   - Story 3.1: Mobile App Foundation (8 SP)
   - Story 3.2: Authentication Screens (5 SP)
   - Story 3.3: Home & Subject Navigation (5 SP)
   - Story 3.4: AI Tutoring Interface (13 SP)
   - Story 3.6: Progress & Profile Screens (5 SP)

---

### P1 - High Priority (Core Features)
**Target:** Weeks 4-10
**Total Stories:** 24
**Total Tasks:** 95

1. **Epic 4: Exercise System**
   - Story 4.1: Exercise Generation Backend (8 SP)
   - Story 4.2: Exercise Submission & Grading (5 SP)
   - Story 4.3: Exercise UI (8 SP)

2. **Epic 5: Parent Dashboard**
   - Story 5.1: Parent Dashboard Backend (5 SP)
   - Story 5.2: Parent Web Portal UI (13 SP)

3. **Epic 6: AI-Generated Reports**
   - Story 6.1: Report Generation Service (8 SP)
   - Story 6.2: Report Delivery (5 SP)

4. **Epic 7: Wallet & Payment Integration**
   - Story 7.1: Paystack Integration (5 SP)
   - Story 7.2: Mobile Money Integration (8 SP)

5. **Epic 9: Security & Compliance**
   - Story 9.1: Security Hardening (5 SP)

---

### P2 - Medium Priority (Nice to Have)
**Target:** Weeks 8-12
**Total Stories:** 12
**Total Tasks:** 32

1. **Epic 7: Wallet Features**
   - Story 7.3: Spending Limits & Alerts (3 SP)

2. **Epic 8: n8n Automation**
   - Story 8.1: Core Automation Workflows (5 SP)
   - Story 8.2: Re-engagement Workflows (3 SP)

3. **Epic 9: Compliance**
   - Story 9.2: COPPA & GDPR Compliance (5 SP)

4. **Epic 13: Admin Tools**
   - Story 13.1: Admin Monitoring Dashboard (5 SP)
   - Story 13.2: Content Moderation Tools (5 SP)
   - Story 13.3: Analytics & Business Intelligence (5 SP)

---

### P3 - Low Priority (Post-MVP)
**Target:** Phase 4 (Future)
**Total Stories:** 11
**Total Tasks:** N/A (Phase 4)

1. **Epic 3: Mobile Voice**
   - Story 3.5: Voice Input (8 SP)

2. **Epic 10: Voice Tutoring (VAPI)** - All stories

3. **Epic 11: Multi-Language Support** - All stories

4. **Epic 12: Offline Mode** - All stories

---

## EFFORT ESTIMATION

### Development Team
- 1 Backend Developer (40 hrs/week)
- 1 Frontend Developer (40 hrs/week)
- 1 Mobile Developer (40 hrs/week)
- 0.5 QA Engineer (20 hrs/week)
- 0.5 DevOps Engineer (20 hrs/week)

### Timeline Breakdown

**Weeks 1-3: Critical Foundation (P0)**
- Testing infrastructure (120 hours)
- RAG pipeline completion (64 hours)
- Total: 184 hours / 3 devs = **3 weeks**

**Weeks 3-8: Mobile App Core (P0)**
- Mobile app foundation (200 hours)
- Tutoring interface (160 hours)
- Total: 360 hours / 2 devs (backend support) = **5 weeks**

**Weeks 5-10: Exercises & Parent Portal (P1)**
- Exercise system (128 hours)
- Parent dashboard (120 hours)
- Reports (80 hours)
- Total: 328 hours / 3 devs = **5 weeks**

**Weeks 8-12: Payments & Security (P1)**
- Payment integration (80 hours)
- Security hardening (64 hours)
- Admin tools (48 hours)
- Total: 192 hours / 2 devs = **4 weeks**

**Total MVP Timeline:** 12-14 weeks (3-3.5 months)

---

## JIRA IMPORT FORMAT

To import into JIRA, use the following CSV format template:

```csv
Issue Type,Summary,Description,Priority,Story Points,Epic Link,Assignee,Status
Epic,Testing & Quality Assurance,"Critical test coverage and CI/CD setup",Highest,31,,,To Do
Story,Backend Unit Test Coverage,"Achieve 80%+ test coverage on backend",Highest,13,Testing & Quality Assurance,,To Do
Task,[TASK-001] Setup pytest coverage tracking,"Install pytest-cov, configure coverage.py, add to CI/CD",Highest,,Backend Unit Test Coverage,,To Do
...
```

---

## SUCCESS METRICS

### Phase 1 Completion Criteria (P0)
- ✅ 80%+ backend test coverage
- ✅ CI/CD pipeline automated
- ✅ RAG material processing working end-to-end
- ✅ Mobile app released to TestFlight/Play Store Beta
- ✅ Students can ask questions and get answers
- ✅ 100 beta testers using the app
- ✅ Answer accuracy >85%

### Phase 2 Completion Criteria (P1)
- ✅ Exercise system functional
- ✅ Parent dashboard live
- ✅ Payment integration working
- ✅ 500+ active students
- ✅ Weekly reports automated
- ✅ Revenue >₵20,000/month

### Production Ready Criteria
- ✅ All P0 and P1 stories completed
- ✅ Security audit passed
- ✅ Load testing completed (1000 concurrent users)
- ✅ 3+ pilot schools converted to paid
- ✅ Parent satisfaction >4/5
- ✅ System uptime >99.5%

---

## NOTES

1. **Dependency Management:** Many tasks depend on others being complete first (especially RAG pipeline before exercises)

2. **Testing is Critical:** The current 10-15% test coverage is the biggest risk. Start with testing immediately.

3. **Mobile App is Blocker:** The student interface is 0% complete and blocks user adoption. Prioritize after testing.

4. **Payment Integration:** Revenue depends on this working smoothly. Test thoroughly.

5. **API Documentation:** Consider adding Swagger/OpenAPI docs (not in this breakdown but recommended).

---

**Document Status:** Ready for JIRA import
**Last Updated:** 2025-11-07
**Total Epics:** 13
**Total Stories:** 62
**Total Tasks:** 187
**Estimated Duration:** 12-14 weeks for MVP (P0 + P1)
