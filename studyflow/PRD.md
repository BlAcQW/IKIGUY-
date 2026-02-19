# StudyFlow (EduMate) - Product Requirements Document

**Product Name:** StudyFlow (EduMate)
**Version:** 1.0
**Date:** 2025-10-24
**Status:** PRD - Ready for Development
**Owner:** KasaAI Platform Team

---

## Executive Summary

StudyFlow (EduMate) is an **AI-powered personal tutoring platform** that provides intelligent, conversational learning experiences using school-specific study materials. The platform combines RAG (Retrieval-Augmented Generation), voice AI, wallet-based billing, and automated workflows to deliver a comprehensive educational solution for African schools.

### Vision Statement

> "Transform every student's learning journey with a personal AI tutor that knows their curriculum, speaks their language, and adapts to their learning pace."

### Key Differentiators

1. **Curriculum-Aligned Learning**: RAG-powered Q&A using actual school study materials
2. **Voice-First Interactions**: Natural conversation in multiple languages (English, Twi, French)
3. **Parent Transparency**: AI-generated weekly reports with actionable insights
4. **Fair Pay-Per-Use**: Wallet-based system that parents control and understand
5. **Automated Workflows**: n8n integration for notifications, reminders, and batch operations
6. **Multi-Language Support**: Built for African classrooms with local language support

---

## Problem Statement

### Current Challenges in African Education

1. **Limited Access to Tutors**:
   - High tutor costs (₵50-100/hour) exclude most families
   - Urban-rural divide in tutor availability
   - Quality inconsistency across tutors

2. **One-Size-Fits-All Teaching**:
   - Large class sizes (40-60 students)
   - Teachers can't provide personalized attention
   - Students struggle at different paces

3. **Curriculum Misalignment**:
   - Generic tutoring apps don't match local curriculum
   - Textbook examples don't reflect local context
   - Language barriers (teaching in English only)

4. **Lack of Parent Visibility**:
   - Parents can't monitor learning progress
   - No visibility into where child struggles
   - Surprise poor performance at end of term

5. **Technology Barriers**:
   - Most families have smartphones, not computers
   - Intermittent internet connectivity
   - Limited tech literacy among parents

---

## Solution Overview

### Core Product Concept

StudyFlow is a **mobile-first AI tutoring platform** that:

1. **Ingests school curriculum** (PDFs, textbooks, notes)
2. **Answers student questions** using RAG (semantically accurate)
3. **Provides practice exercises** with instant feedback
4. **Tracks learning progress** across subjects and topics
5. **Generates weekly reports** for parents with AI insights
6. **Bills per usage** through a wallet system parents control
7. **Automates workflows** for reminders, reports, and notifications

### How It Works

```
┌────────────────────────────────────────────────────────────┐
│                  StudyFlow Ecosystem                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  School/Teacher uploads curriculum materials (PDF/DOCX)    │
│           ↓                                                 │
│  System processes, chunks, and embeds using RAG            │
│           ↓                                                 │
│  Student asks questions (voice or text)                    │
│           ↓                                                 │
│  AI Tutor searches curriculum + generates answer           │
│           ↓                                                 │
│  Student completes practice exercises                      │
│           ↓                                                 │
│  System tracks progress + deducts wallet credits           │
│           ↓                                                 │
│  Weekly AI report sent to parent (email/WhatsApp)          │
│           ↓                                                 │
│  Parent reviews progress + tops up wallet if needed        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## User Personas

### 1. Student - "Kofi" (Primary User)

**Demographics:**
- Age: 10-18 years old
- Grade: Primary 4 - Form 4 (SHS)
- Device: Smartphone (shared or personal)
- Location: Urban or peri-urban Ghana

**Goals:**
- Understand difficult concepts from class
- Practice before exams
- Get instant help with homework
- Learn at own pace without judgment

**Pain Points:**
- Can't afford private tutor
- Too shy to ask questions in class
- Parents can't help with advanced subjects
- Limited time after school (chores, work)

**Usage Patterns:**
- Uses app 15-30 minutes per day
- Prefers voice over typing
- Uses mostly in evening (after school)
- Needs offline access for downloaded materials

---

### 2. Parent - "Akosua" (Payer & Monitor)

**Demographics:**
- Age: 30-50 years old
- Occupation: Market trader, office worker, teacher
- Income: ₵1,500-5,000/month
- Device: Smartphone
- Tech Literacy: Basic to intermediate

**Goals:**
- Help child succeed academically
- Monitor child's learning progress
- Control spending on education
- Understand where child needs help

**Pain Points:**
- Can't afford private tutors
- No visibility into child's struggles
- Surprise poor grades at end of term
- Doesn't know how to help with homework

**Usage Patterns:**
- Checks reports weekly
- Tops up wallet monthly (₵20-50)
- Uses web portal (not mobile app)
- Shares reports with child's teacher

---

### 3. Teacher/Admin - "Mr. Mensah" (Content Manager)

**Demographics:**
- Age: 25-55 years old
- Role: Class teacher, Head of Department, School Admin
- Device: Laptop or desktop computer
- Tech Literacy: Intermediate to advanced

**Goals:**
- Provide additional learning support to students
- Reduce repetitive questions
- Track class performance
- Identify struggling students early

**Pain Points:**
- Too many students per class
- Limited time for individual attention
- No tools to track student understanding
- Curriculum materials scattered (PDFs, printouts)

**Usage Patterns:**
- Uploads materials once per term
- Reviews class analytics monthly
- Uses reports to identify intervention needs
- Communicates with parents through reports

---

## Core Features & Requirements

### Feature 1: Admin/Teacher Upload Portal

**Purpose:** Allow teachers to upload and manage curriculum materials

**User Story:**
> "As a teacher, I want to upload my class notes and textbooks so that my students can get accurate answers based on what I taught."

**Functional Requirements:**

1. **Material Upload**
   - Accept PDF, DOCX, TXT, MD formats
   - Drag-and-drop file upload
   - Batch upload support (multiple files at once)
   - File size limit: 50MB per file
   - Max 100 files per batch

2. **Material Tagging & Organization**
   - Required fields: Subject, Topic, Grade, Difficulty
   - Optional fields: Chapter, Page Range, Keywords
   - Auto-detect subject/topic from filename
   - Tag multiple files with same metadata (batch tagging)

3. **Material Processing**
   - Auto-process PDFs using `@shared/integration/document_processor.py`
   - Extract text, images, and tables
   - Chunk intelligently (sentence-aware, paragraph-aware)
   - Embed using `@shared/integration/rag.py`
   - Store in pgvector for semantic search

4. **Material Management**
   - View uploaded materials (list, grid, search)
   - Edit metadata (subject, topic, tags)
   - Delete materials (with confirmation)
   - Re-process materials (if chunking improved)
   - Preview material content before publishing

5. **Knowledge Base Organization**
   - One collection per school+subject combination
   - Example: `school_123_mathematics`, `school_123_science`
   - Support multiple grades in same collection (filtered by metadata)

**Technical Requirements:**

```python
# Using shared services
from apps.shared.integration.document_processor import (
    DocumentProcessor,
    ChunkingStrategy
)
from apps.shared.integration.rag import (
    RAGService,
    create_rag_service_from_env
)

# Initialize services
doc_processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.SENTENCE_AWARE,
    chunk_size=800,  # Smaller chunks for Q&A
    chunk_overlap=200,
    extract_metadata=True
)

rag_service = await create_rag_service_from_env(ai_provider="gemini")
```

**Acceptance Criteria:**

- [ ] Teacher can upload PDF/DOCX files successfully
- [ ] System extracts text with >95% accuracy
- [ ] Materials are chunked and embedded within 60 seconds
- [ ] Teacher can search uploaded materials by subject/topic
- [ ] Teacher can preview material content before publishing
- [ ] System handles errors gracefully (corrupt files, too large, etc.)

---

### Feature 2: AI Tutor (Student Learning Experience)

**Purpose:** Provide conversational Q&A and explanations based on curriculum

**User Story:**
> "As a student, I want to ask questions about my homework and get clear explanations based on what my teacher taught."

**Functional Requirements:**

1. **Question Asking**
   - Text input (keyboard)
   - Voice input (speech-to-text)
   - Language selection (English, Twi, French)
   - Question history (last 20 questions)
   - Save favorite questions

2. **Answer Generation**
   - RAG-powered answers from curriculum materials
   - Confidence score display (High, Medium, Low)
   - Source citations (which page/document)
   - "Explain simpler" button (adaptive difficulty)
   - "Related topics" suggestions

3. **AI Tutor Persona**
   - Name: "Tutor Ama"
   - Tone: Warm, patient, encouraging
   - Adaptive: Adjusts language to student's grade level
   - Context-aware: Knows student's past performance
   - Multilingual: English, Twi, French

4. **Conversation Management**
   - Session-based conversations (start/end)
   - Context retention (remembers previous questions)
   - Conversation export (share with parent/teacher)
   - Cost display (credits used per question)

5. **Voice Interaction (Optional - Phase 2)**
   - Text-to-speech for answers (using Voice Lab)
   - Speech-to-text for questions (using Whisper)
   - Voice cloning for personalized tutor voice
   - VAPI integration for full conversational tutoring

**Technical Requirements:**

```python
# Using shared RAG service
from apps.shared.integration.rag import RAGService

rag = await create_rag_service_from_env(ai_provider="gemini")

result = await rag.query_knowledge_base(
    collection_name=f"school_{school_id}_{subject}",
    query=question,
    context={
        "student_grade": student.grade,
        "student_performance": student.avg_score,
        "preferred_explanation_style": "simple"
    },
    filters={
        "grade": student.grade,
        "subject": subject
    },
    system_prompt_template="""
    You are Tutor Ama, a friendly and patient AI tutor for {student_grade} students.
    Answer based on the provided study materials.

    Guidelines:
    - Use simple language for {student_grade} students
    - Break down complex concepts into steps
    - Provide examples when helpful
    - Encourage the student
    - Always cite sources
    """
)
```

**Acceptance Criteria:**

- [ ] Student can type or speak questions
- [ ] System returns relevant answers within 5 seconds
- [ ] Answers cite specific pages/sections from curriculum
- [ ] Confidence score shown for each answer
- [ ] "Explain simpler" adjusts language appropriately
- [ ] Cost per question displayed clearly
- [ ] System handles low-confidence answers gracefully (flag for review)

---

### Feature 3: Practice Exercises & Feedback

**Purpose:** Auto-generate exercises from curriculum and provide instant feedback

**User Story:**
> "As a student, I want to practice what I learned and get instant feedback so I know what I'm getting wrong."

**Functional Requirements:**

1. **Exercise Generation**
   - Auto-generate MCQs from study materials (using RAG)
   - Question types: Multiple choice, True/False, Short answer
   - Configurable difficulty (Easy, Medium, Hard)
   - Configurable length (5, 10, 15, 20 questions)
   - Topic-specific exercises

2. **Exercise Taking**
   - Timer display (optional countdown)
   - Save progress (pause and resume)
   - Review before submit
   - Hint system (costs extra credits)

3. **Auto-Grading & Feedback**
   - Instant grading for MCQs
   - AI grading for short answers (using LLM)
   - Explanation for incorrect answers
   - Show correct answer + reasoning
   - Performance summary (score, time, accuracy)

4. **Exercise Analytics**
   - Score history per subject
   - Topic mastery visualization
   - Weak areas identification
   - Improvement trends over time

5. **Adaptive Difficulty**
   - Start at student's grade level
   - Increase difficulty if >80% score
   - Decrease difficulty if <60% score
   - Recommend topics to review

**Technical Requirements:**

```python
# Exercise generation using RAG
result = await rag.query_knowledge_base(
    collection_name=f"school_{school_id}_{subject}",
    query=f"Generate {num_questions} {difficulty} MCQs about {topic}",
    context={
        "task": "generate_exercise",
        "student_grade": student.grade,
        "difficulty": difficulty,
        "num_questions": num_questions
    },
    system_prompt_template="""
    Generate {num_questions} multiple-choice questions for {student_grade} students
    about {topic} at {difficulty} difficulty.

    Format:
    Question 1: [question text]
    A) [option]
    B) [option]
    C) [option]
    D) [option]
    Correct Answer: [A/B/C/D]
    Explanation: [why this is correct]
    """
)
```

**Acceptance Criteria:**

- [ ] System generates 5-20 MCQs within 10 seconds
- [ ] Questions are relevant to selected topic
- [ ] Questions match selected difficulty level
- [ ] Instant feedback provided after submission
- [ ] Student can review past exercises
- [ ] Adaptive difficulty adjusts based on performance

---

### Feature 4: Wallet & Billing System

**Purpose:** Pay-per-use credit system controlled by parents

**User Story:**
> "As a parent, I want to control how much my child spends on tutoring and see exactly where the money goes."

**Functional Requirements:**

1. **Wallet Creation**
   - Auto-create wallet on parent registration
   - Currency: GHS (Ghana Cedis)
   - Welcome bonus: ₵20 (100 minutes of tutoring)
   - Multiple wallets (one per student)

2. **Top-Up Methods**
   - Mobile Money (MTN, Vodafone, AirtelTigo)
   - Paystack (credit/debit card)
   - Stripe (international cards)
   - Minimum top-up: ₵10
   - Recommended amounts: ₵20, ₵50, ₵100, ₵200

3. **Usage Tracking**
   - Cost per Q&A interaction (₵0.20 = 1 minute)
   - Cost per exercise feedback (₵0.50 = 2.5 minutes)
   - Cost per hint (₵0.10 = 30 seconds)
   - Real-time balance display
   - Transaction history (past 3 months)

4. **Spending Controls**
   - Daily spending limit (₵5/day default)
   - Weekly spending limit (₵20/week default)
   - Low balance alert (₵5 remaining)
   - Out of credits → block access (with grace message)

5. **Refunds & Adjustments**
   - Request refund for unused credits
   - System errors → auto-credit refund
   - Promo codes for discounts
   - Referral bonuses

**Technical Requirements:**

```python
# Using shared wallet service
from apps.shared.integration.wallet import (
    WalletService,
    create_wallet_service_from_env
)
from apps.shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier
)

wallet_service = await create_wallet_service_from_env()
usage_calculator = UsageCalculator(tier=PricingTier.BASIC)

# Create wallet
parent_wallet = await wallet_service.create_wallet(
    user_id=str(parent.id),
    currency="GHS",
    initial_balance=Decimal("20.00")
)

# Deduct cost per interaction
cost = usage_calculator.calculate_rag_cost(
    input_tokens=500,
    output_tokens=200,
    num_queries=1,
    provider="gemini",
    model="gemini-pro"
)

await wallet_service.debit(
    wallet_id=parent_wallet.wallet_id,
    amount=cost.total_cost,
    description=f"Tutoring: {subject} - {student.name}",
    idempotency_key=f"qa-{session_id}",
    allow_negative=False
)
```

**Acceptance Criteria:**

- [ ] Parent can top up wallet via MoMo/Paystack
- [ ] Real-time balance displayed to parent and student
- [ ] Cost deducted immediately after each interaction
- [ ] Transaction history shows clear descriptions
- [ ] Low balance alert sent via SMS/WhatsApp
- [ ] Spending limits enforced automatically
- [ ] Refund requests processed within 24 hours

---

### Feature 5: Parent Dashboard & Reports

**Purpose:** Provide parents with visibility into child's learning progress

**User Story:**
> "As a parent, I want to see how my child is performing, where they struggle, and what I should focus on."

**Functional Requirements:**

1. **Dashboard Overview**
   - Wallet balance (current + last top-up)
   - This week's learning stats (time, questions, exercises)
   - Student performance summary (overall score)
   - Weak areas identification
   - Upcoming exercises/reminders

2. **Weekly AI-Generated Reports**
   - Sent every Sunday evening via email/WhatsApp
   - Report sections:
     - Overall summary (2-3 sentences)
     - Time spent per subject (chart)
     - Questions asked per subject
     - Exercises completed + average score
     - Strengths (what child is doing well)
     - Areas for improvement (where child struggles)
     - Recommendations (specific actions for parent)
   - Download as PDF
   - Share with teacher

3. **Performance Analytics**
   - Score trends over time (line chart)
   - Subject comparison (bar chart)
   - Topic mastery heatmap
   - Time spent per subject (pie chart)
   - Learning streak (consecutive days)

4. **Usage Analytics**
   - Cost breakdown per subject
   - Daily spending chart
   - Average cost per session
   - Projected monthly cost

5. **Controls & Settings**
   - Set daily/weekly spending limits
   - Enable/disable subjects
   - Schedule learning reminders
   - Configure report delivery (email, WhatsApp, SMS)
   - Manage notifications

**Technical Requirements:**

```python
# AI report generation using RAG
from apps.shared.integration.rag import RAGService

# Generate weekly report
result = await rag.query_knowledge_base(
    collection_name="educational_insights",
    query="Generate weekly report",
    context={
        "statistics": stats,
        "subject_performance": subject_performance
    },
    system_prompt_template="""
    You are an educational analyst generating a weekly progress report for parents.

    Based on student performance data, provide:
    1. Overall summary (2-3 sentences)
    2. Strengths (what student is doing well)
    3. Areas for improvement (what needs focus)
    4. Specific recommendations (actionable tips)

    Be encouraging and constructive.
    """
)
```

**Acceptance Criteria:**

- [ ] Parent receives weekly report every Sunday
- [ ] Report shows clear performance metrics
- [ ] AI summary is relevant and actionable
- [ ] Parent can download report as PDF
- [ ] Analytics charts are easy to understand
- [ ] Spending limit changes take effect immediately

---

### Feature 6: Workflow Automation (n8n Integration)

**Purpose:** Automate repetitive tasks and notifications using n8n workflows

**User Story:**
> "As an admin, I want to automate report generation, reminders, and notifications so the system runs smoothly without manual intervention."

**Functional Requirements:**

1. **Automated Workflows**
   - Weekly report generation (every Sunday 6pm)
   - Low balance alerts (when balance < ₵5)
   - Daily learning reminders (customizable time)
   - Exercise completion reminders (if no activity for 3 days)
   - Birthday wishes for students
   - Monthly performance summaries for teachers

2. **Notification Channels**
   - Email (via SendGrid/SMTP)
   - WhatsApp (via WhatsApp Business API)
   - SMS (via Twilio/Vonage)
   - In-app notifications (push notifications)

3. **Workflow Templates**
   - Welcome sequence (3 emails over first week)
   - Onboarding checklist reminders
   - Payment reminder (3 days before wallet depletes)
   - Re-engagement campaign (if inactive for 7 days)
   - Referral program automation

4. **Admin Workflow Management**
   - View active workflows
   - Enable/disable workflows
   - Test workflows before activation
   - View workflow logs and errors
   - Edit workflow triggers and actions

**Technical Requirements:**

```python
# Using shared n8n integration
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration(
    base_url=os.getenv("N8N_URL"),
    api_key=os.getenv("N8N_API_KEY")
)

# Trigger workflow for weekly report
await n8n.trigger_workflow(
    workflow_name="weekly_student_report",
    data={
        "student_id": str(student.id),
        "parent_email": parent.email,
        "parent_phone": parent.phone,
        "report_data": report_json
    }
)
```

**Acceptance Criteria:**

- [ ] Weekly reports sent automatically every Sunday
- [ ] Low balance alerts sent within 5 minutes of threshold
- [ ] Daily reminders sent at parent-configured time
- [ ] Admin can view workflow execution logs
- [ ] Failed workflows retry automatically (3 attempts)
- [ ] Notifications delivered via multiple channels

---

## Non-Functional Requirements

### Performance

- **Response Time**:
  - Q&A response < 5 seconds (95th percentile)
  - Exercise generation < 10 seconds
  - Document upload processing < 60 seconds per file

- **Scalability**:
  - Support 10,000 concurrent students
  - Handle 100,000 questions per day
  - Process 1,000 document uploads per day

- **Availability**:
  - 99.5% uptime (target)
  - Scheduled maintenance windows (Sunday 2am-4am)

### Security

- **Authentication**: Supabase Auth (email, phone, password)
- **Authorization**: Role-based access control (Student, Parent, Teacher, Admin)
- **Data Encryption**:
  - At rest: MongoDB encryption
  - In transit: HTTPS/TLS 1.3
- **PII Protection**: Encrypt student names, phone numbers, emails
- **COPPA Compliance**: Parent consent for students <13 years old
- **GDPR Compliance**: Data export and deletion on request

### Usability

- **Mobile-First**: Optimized for smartphones (iOS, Android)
- **Accessibility**: WCAG 2.1 AA compliance
- **Languages**: English, Twi, French (Phase 1)
- **Offline Support**: Cache downloaded materials (Phase 2)
- **Low Bandwidth**: Works on 2G/3G networks

### Reliability

- **Data Backup**: Daily MongoDB backups (7-day retention)
- **Error Handling**: Graceful degradation (show cached content if AI unavailable)
- **Monitoring**: Real-time alerts for system failures
- **Disaster Recovery**: 24-hour RTO, 1-hour RPO

---

## Technical Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Mobile App** | React Native (Expo) | Cross-platform mobile app |
| **Admin Portal** | Next.js / React | Web portal for teachers |
| **Parent Dashboard** | Next.js / React | Web portal for parents |
| **Backend API** | FastAPI (Python 3.10+) | REST API |
| **Database** | MongoDB | Users, sessions, exercises |
| **Auth** | Supabase (PostgreSQL) | Authentication |
| **Vector DB** | pgvector (Supabase) | RAG embeddings |
| **Wallet** | MongoDB + Paystack/MoMo | Payment processing |
| **AI Provider** | Gemini Pro (primary), OpenAI (fallback) | LLM for RAG |
| **Voice (Optional)** | Whisper (ASR), Voice Lab (TTS), VAPI | Voice interactions |
| **Automation** | n8n | Workflow automation |
| **Hosting** | VPS (KasaAI infrastructure) | Backend hosting |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    StudyFlow Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend Layer:                                             │
│  ├─ Mobile App (React Native)        → Students            │
│  ├─ Admin Portal (Next.js)           → Teachers            │
│  └─ Parent Dashboard (Next.js)       → Parents             │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  API Layer (FastAPI):                                        │
│  ├─ /api/auth           → Authentication                   │
│  ├─ /api/materials      → Upload & management              │
│  ├─ /api/tutoring       → Q&A & conversations              │
│  ├─ /api/exercises      → Exercise generation & grading    │
│  ├─ /api/wallet         → Payments & usage                 │
│  ├─ /api/reports        → Progress reports                 │
│  └─ /api/webhooks       → n8n, VAPI, Payment webhooks      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Shared Services Layer (@apps/shared/integration/):         │
│  ├─ RAGService          → Knowledge base Q&A               │
│  ├─ DocumentProcessor   → PDF/DOCX processing              │
│  ├─ WalletService       → Credit management                │
│  ├─ UsageCalculator     → Cost calculation                 │
│  ├─ AIProviderService   → AI provider management           │
│  ├─ VAPIService         → Voice tutoring (optional)        │
│  └─ N8NIntegration      → Workflow automation              │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Data Layer:                                                 │
│  ├─ MongoDB             → Users, materials, sessions       │
│  ├─ PostgreSQL          → Supabase auth + pgvector         │
│  └─ Supabase Storage    → PDF/DOCX file storage            │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  External Services:                                          │
│  ├─ Gemini Pro          → LLM for RAG                      │
│  ├─ Paystack/MoMo       → Payment gateways                 │
│  ├─ n8n                 → Workflow engine                   │
│  ├─ WhatsApp API        → Notifications                     │
│  └─ SendGrid/SMTP       → Email delivery                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Pricing Model

### Student/Parent Pricing

| Tier | Description | Price |
|------|-------------|-------|
| **Free Trial** | 30 minutes of tutoring | Free |
| **Pay-as-you-learn** | Top-up as needed | ₵20 = 100 minutes |
| **Monthly Plan** | Unlimited tutoring | ₵50/month per student |
| **Family Plan** | 2-3 students | ₵80/month |

### School/Enterprise Pricing

| Tier | Description | Price |
|------|-------------|-------|
| **School Plan** | Bulk pricing for schools | ₵30/student/month (min 50 students) |
| **District Plan** | Multiple schools | ₵25/student/month (min 500 students) |
| **Enterprise** | Custom features, white-label | Custom pricing |

### Revenue Model

**Year 1 (Pilot):**
- 5 schools × 200 students = 1,000 students
- Average spend: ₵40/month per student
- Monthly revenue: ₵40,000
- Annual revenue: ₵480,000

**Year 2 (Growth):**
- 50 schools × 300 students = 15,000 students
- Average spend: ₵40/month per student
- Monthly revenue: ₵600,000
- Annual revenue: ₵7,200,000

---

## Success Metrics

### User Engagement Metrics

- **Daily Active Students (DAS)**: Target 60% of enrolled students
- **Average Session Duration**: Target 20 minutes
- **Questions Asked per Session**: Target 5-10
- **Exercises Completed per Week**: Target 3-5
- **Learning Streak**: Target 3+ consecutive days

### Learning Outcome Metrics

- **Average Exercise Score**: Target >70%
- **Score Improvement**: Target +10% month-over-month
- **Topic Mastery Rate**: Target 80% (score >80% on topic)
- **Concept Retention**: Target 70% (retest after 2 weeks)

### Business Metrics

- **Monthly Active Students (MAS)**: Target 80% of enrolled students
- **Average Wallet Top-Up**: Target ₵50/month
- **Revenue per Student**: Target ₵40/month
- **Parent Satisfaction Score**: Target 4.5/5
- **School Retention Rate**: Target 90% annual renewal

### Technical Metrics

- **API Response Time (p95)**: Target <5 seconds
- **System Uptime**: Target 99.5%
- **RAG Answer Accuracy**: Target >85% (verified by teachers)
- **Error Rate**: Target <1%

---

## Go-to-Market Strategy

### Phase 1: Pilot Program (Months 1-3)

**Target:**
- 3-5 schools in Greater Accra
- 500-1,000 students
- Free trial for all pilot schools

**Goals:**
- Validate product-market fit
- Collect user feedback
- Measure learning outcomes
- Refine AI answer quality

**Activities:**
- School partnerships (MOUs)
- Teacher training workshops
- Parent orientation sessions
- Weekly feedback calls

---

### Phase 2: Regional Expansion (Months 4-12)

**Target:**
- 50 schools across Ghana
- 15,000 students
- Convert 30% of pilot schools to paid plans

**Goals:**
- Scale infrastructure
- Achieve profitability
- Build brand awareness
- Optimize pricing model

**Activities:**
- Paid marketing campaigns
- School referral program
- Parent testimonials
- Teacher ambassador program

---

### Phase 3: Pan-African Expansion (Year 2+)

**Target:**
- Nigeria, Kenya, South Africa
- 100,000+ students
- Enterprise partnerships

**Goals:**
- Market leadership in Africa
- International funding
- White-label partnerships
- Government contracts

---

## Risk Analysis & Mitigation

### Risk 1: Low Answer Accuracy

**Risk:** RAG answers are inaccurate or irrelevant
**Impact:** High (parents lose trust, students fail exams)
**Mitigation:**
- Teacher review panel for low-confidence answers
- Continuous feedback loop for prompt improvement
- Human tutor escalation option (Phase 2)
- 85% accuracy target before launch

---

### Risk 2: Parent Affordability

**Risk:** Parents can't afford ₵40/month
**Impact:** Medium (low adoption, high churn)
**Mitigation:**
- Free trial (30 minutes)
- Flexible pay-as-you-learn option
- Scholarship program for low-income families
- School subsidies (bulk pricing)

---

### Risk 3: Network Connectivity

**Risk:** Intermittent internet in rural areas
**Impact:** Medium (poor UX, high drop-off)
**Mitigation:**
- Offline mode (cache materials)
- Low-bandwidth mode (text-only)
- USSD fallback for balance checks
- SMS-based Q&A (Phase 2)

---

### Risk 4: Content Copyright

**Risk:** Schools upload copyrighted textbooks
**Impact:** High (legal liability)
**Mitigation:**
- Terms of service (schools certify rights)
- DMCA takedown process
- Partner with publishers for licensed content
- User education on copyright

---

### Risk 5: AI Hallucination

**Risk:** AI generates false information
**Impact:** High (students learn wrong concepts)
**Mitigation:**
- RAG-only mode (no creative generation)
- Confidence scoring (flag low-confidence)
- Source citation requirement
- Teacher flagging system

---

## Appendices

### Appendix A: User Flows

**Student Learning Flow:**
1. Open app → See subjects
2. Select subject (e.g., Mathematics)
3. Choose option: Ask question OR Take exercise
4. If Ask question:
   - Type or speak question
   - Receive answer with sources
   - Rate answer quality
   - Credits deducted
5. If Take exercise:
   - Select topic and difficulty
   - Answer questions
   - Receive instant feedback
   - View score and explanations

**Parent Monitoring Flow:**
1. Log in to dashboard
2. View wallet balance
3. Review this week's activity
4. Read AI-generated report
5. Identify weak areas
6. Top up wallet if needed
7. Share report with teacher

**Teacher Upload Flow:**
1. Log in to admin portal
2. Click "Upload Materials"
3. Drag-and-drop PDF files
4. Tag with subject, topic, grade
5. Preview processed chunks
6. Publish to students
7. Monitor usage analytics

---

### Appendix B: API Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/phone
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

**Materials:**
- `POST /api/materials/upload` - Upload study material
- `GET /api/materials` - List uploaded materials
- `GET /api/materials/{id}` - Get material details
- `PATCH /api/materials/{id}` - Update material metadata
- `DELETE /api/materials/{id}` - Delete material

**Tutoring:**
- `POST /api/tutoring/sessions` - Start tutoring session
- `POST /api/tutoring/ask` - Ask question (RAG query)
- `GET /api/tutoring/sessions/{id}` - Get session details
- `GET /api/tutoring/history` - Get question history

**Exercises:**
- `POST /api/exercises/generate` - Generate exercise
- `POST /api/exercises/{id}/submit` - Submit answers
- `GET /api/exercises/{id}/results` - Get exercise results
- `GET /api/exercises/history` - Get past exercises

**Wallet:**
- `GET /api/wallet/balance` - Get wallet balance
- `POST /api/wallet/topup` - Initiate top-up
- `GET /api/wallet/transactions` - Get transaction history
- `POST /api/wallet/webhook` - Payment webhook handler

**Reports:**
- `GET /api/reports/weekly/{student_id}` - Get weekly report
- `GET /api/reports/performance/{student_id}` - Get performance analytics
- `POST /api/reports/generate` - Manually trigger report generation

---

### Appendix C: Database Schemas

See `PLANNING.md` for detailed database schemas.

---

### Appendix D: Shared Services Integration

**Development Time Savings:**

| Service | Lines of Code | Time Saved |
|---------|--------------|------------|
| RAGService | 750+ lines | 4-5 weeks |
| DocumentProcessor | 600+ lines | 2-3 weeks |
| WalletService | 900+ lines | 3-4 weeks |
| UsageCalculator | 600+ lines | 1-2 weeks |
| AIProviderService | 500+ lines | 2-3 weeks |
| N8NIntegration | 600+ lines | 2-3 weeks |
| VAPIService (optional) | 1100+ lines | 4-5 weeks |

**Total Time Saved:** 14-20 weeks (3.5-5 months) with voice, 10-15 weeks (2.5-3.75 months) without voice

---

## Document Control

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | KasaAI Team | Initial PRD created |

**Approvals:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Business Owner | | | |

**Next Review:** 2025-11-24 (1 month)

---

**End of PRD**
