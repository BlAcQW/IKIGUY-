# EduMate - Planning & Architecture

**Version:** 1.0
**Last Updated:** 2025-10-24
**Status:** Initial Planning

---

## 🎯 Vision

**EduMate** is a mobile-first, AI-powered personal tutoring platform that provides intelligent, conversational learning experiences using school-specific study materials.

**Tagline:** *Your personal tutor that listens, explains, and helps you learn smarter.*

**Core Value Proposition:**
- RAG-powered tutoring using uploaded school materials
- Voice and text-based conversational learning
- Practice exercises with instant feedback
- Parent dashboard with weekly progress reports
- Pay-per-use wallet system (parents control spending)
- Multi-language support (English, Twi, French)

---

## 🏗️ System Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile App** | React Native (Expo) | Cross-platform, shared codebase, student-friendly UX |
| **Admin Portal** | Next.js / React | School admins need desktop access for uploads |
| **Parent Dashboard** | Next.js / React | Web-based, accessible from any device |
| **Backend API** | FastAPI (Python) | Consistent with KasaAI stack, async support, AI-friendly |
| **Database** | MongoDB | Flexible schema for users, classes, exercises, progress |
| **Authentication** | Supabase Auth | Phone + email + password, role-based access |
| **Shared Services** | **✓ RAG** (`apps/shared/integration/rag.py`)<br>**✓ DocumentProcessor** (`apps/shared/integration/document_processor.py`)<br>**✓ Wallet** (`apps/shared/integration/wallet.py`)<br>**✓ UsageCalculator** (`apps/shared/integration/usage_calculator.py`)<br>**✓ VAPI** (optional for advanced tutoring) | Q&A from study materials, PDF processing, payment system, cost tracking, voice tutoring |
| **Vector Database** | PostgreSQL + pgvector | Semantic search over study materials |
| **Voice AI** | - Text-to-Speech: KasaAI Voice Lab<br>- Speech-to-Text: Whisper<br>- Optional: **VAPI** for conversational tutoring | Voice interactions, multilingual support |
| **File Storage** | Supabase Storage | Study materials (PDFs, slides), profile images |
| **Hosting** | Backend: VPS (existing KasaAI infrastructure)<br>Mobile: Expo EAS | Cost-effective, controlled environment |

---

### Shared Services Integration

EduMate maximizes reuse of KasaAI's shared services to accelerate development:

**✓ RAG Service** (`apps/shared/integration/rag.py`)
- Q&A from uploaded study materials
- Semantic search over curriculum content
- Multi-provider AI support (OpenAI, Gemini, Anthropic)
- Confidence scoring for answer quality
- Context-aware responses with citation
- **750+ lines** of production-ready code
- **Development time saved: 4-5 weeks**

**✓ Document Processor** (`apps/shared/integration/document_processor.py`)
- PDF/DOCX/TXT processing for study materials
- Intelligent chunking (4 strategies: recursive, sentence-aware, paragraph-aware, fixed-size)
- Metadata extraction (title, page numbers, sections)
- Batch processing for multiple documents
- **600+ lines** of production-ready code
- **Development time saved: 2-3 weeks**

**✓ Wallet Service** (`apps/shared/integration/wallet.py`)
- Pay-per-use credit system for parents
- Multi-gateway support (Paystack, Stripe, MoMo)
- Idempotent transaction handling
- Usage limits and balance alerts
- Transaction history and refunds
- **900+ lines** of production-ready code
- **Development time saved: 3-4 weeks**

**✓ Usage Calculator** (`apps/shared/integration/usage_calculator.py`)
- Cost tracking for tutoring minutes
- Cost tracking for exercise feedback
- Tiered pricing support (Free, Basic, Premium, School)
- Detailed cost breakdowns per student
- **600+ lines** of production-ready code
- **Development time saved: 1-2 weeks**

**✓ VAPI Service** (Optional - `apps/shared/integration/vapi.py`)
- Advanced conversational voice tutoring
- Real-time voice interaction with function calling
- Adaptive tutoring based on student responses
- **1100+ lines** of production-ready code
- **Development time saved: 4-5 weeks if used**

**Total Development Time Saved: 10-14 weeks (2.5-3.5 months) without VAPI, 14-19 weeks (3.5-4.75 months) with VAPI**

---

## 🎨 Core Modules

### 1. **Authentication & User Management**

**Features:**
- Multi-role authentication (Student, Parent, Teacher, Admin)
- Phone + email + password login
- Student profiles linked to parent accounts
- School/organization management
- Class and grade assignments

**Database Schema:**
```python
User:
  - id: ObjectId
  - email: str (unique, indexed)
  - phone: str (optional)
  - name: str
  - role: str  # "student", "parent", "teacher", "admin"
  - organization_id: ObjectId (ref: School)
  - created_at: datetime
  - last_active: datetime
  - profile_image_url: str (optional)

Student:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - parent_id: ObjectId (ref: Parent)
  - grade: str  # "Grade 9", "Form 3", etc.
  - class_id: ObjectId (ref: Class)
  - learning_preferences: dict  # {"voice_enabled": true, "difficulty_level": "medium"}
  - wallet_id: str (managed by parent)
  - created_at: datetime

Parent:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - students: List[ObjectId] (refs: Student)
  - wallet_id: str (ref: Wallet service)
  - created_at: datetime

Teacher:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - subjects: List[str]
  - classes: List[ObjectId] (refs: Class)
  - created_at: datetime

School:
  - id: ObjectId
  - name: str
  - location: str
  - contact_email: str
  - contact_phone: str
  - created_at: datetime
  - plan_type: str  # "trial", "school_plan", "enterprise"

Class:
  - id: ObjectId
  - school_id: ObjectId (ref: School)
  - name: str  # "Grade 9A", "Form 3 Science"
  - grade: str
  - teacher_ids: List[ObjectId] (refs: Teacher)
  - student_ids: List[ObjectId] (refs: Student)
  - created_at: datetime
```

---

### 2. **Admin/Teacher Upload Portal**

**Features:**
- Upload study materials (PDF, DOCX, slides)
- Tag by subject, topic, grade, difficulty
- Auto-processing with DocumentProcessor
- Auto-embedding with RAG service
- Material management (edit, delete, replace)
- Preview materials before publishing to students

**Material Processing Flow:**
```python
from apps.shared.integration.document_processor import DocumentProcessor, ChunkingStrategy
from apps.shared.integration.rag import RAGService, create_rag_service_from_env

# Initialize services
doc_processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.SENTENCE_AWARE,
    chunk_size=800,  # Smaller chunks for Q&A
    chunk_overlap=200,
    extract_metadata=True
)

rag_service = await create_rag_service_from_env(ai_provider="gemini")

async def upload_study_material(
    file_path: str,
    subject: str,
    topic: str,
    grade: str,
    difficulty: str,
    school_id: str
):
    """Process and embed uploaded study material."""

    # Step 1: Process document (extract text, chunk, extract metadata)
    processed_doc = await doc_processor.process_file(file_path)

    # Step 2: Store material metadata in MongoDB
    material = await db.study_materials.insert_one({
        "school_id": ObjectId(school_id),
        "subject": subject,
        "topic": topic,
        "grade": grade,
        "difficulty": difficulty,
        "filename": processed_doc.filename,
        "file_url": await upload_to_storage(file_path),
        "num_chunks": len(processed_doc.chunks),
        "metadata": processed_doc.metadata,
        "created_at": datetime.utcnow()
    })

    # Step 3: Prepare knowledge documents for RAG
    knowledge_docs = [
        {
            "content": chunk.content,
            "metadata": {
                "material_id": str(material.inserted_id),
                "subject": subject,
                "topic": topic,
                "grade": grade,
                "difficulty": difficulty,
                "school_id": school_id,
                "page_number": chunk.metadata.get("page_number"),
                "section": chunk.metadata.get("section")
            }
        }
        for chunk in processed_doc.chunks
    ]

    # Step 4: Initialize knowledge base in RAG service
    collection_name = f"school_{school_id}_{subject.lower().replace(' ', '_')}"
    await rag_service.initialize_knowledge_base(
        collection_name=collection_name,
        documents=knowledge_docs
    )

    return material.inserted_id
```

**Database Schema:**
```python
StudyMaterial:
  - id: ObjectId
  - school_id: ObjectId (ref: School)
  - subject: str  # "Mathematics", "Science", "English"
  - topic: str  # "Algebra", "Photosynthesis", "Grammar"
  - grade: str
  - difficulty: str  # "easy", "medium", "hard"
  - filename: str
  - file_url: str
  - num_chunks: int
  - metadata: dict
  - uploaded_by: ObjectId (ref: Teacher)
  - created_at: datetime
  - last_updated: datetime
  - status: str  # "processing", "ready", "error"
```

---

### 3. **AI Tutor (Student Learning Experience)**

**Features:**
- Conversational Q&A powered by RAG
- Voice and text interactions
- Adaptive explanations ("Explain like I'm 12")
- Practice exercises with instant feedback
- Progress tracking and learning analytics
- Gamification (stars, badges, streaks)

**AI Tutor Persona - "Tutor Ama":**
```
Name: Tutor Ama
Tone: Warm, patient, encouraging
Language: English (primary), Twi, French
Context-aware: Knows student's grade, past performance, learning preferences
Adaptive: Adjusts difficulty based on student responses
```

**Tutoring Session Flow with RAG:**

```python
from apps.shared.integration.rag import RAGService
from apps.shared.integration.usage_calculator import UsageCalculator
from apps.shared.integration.wallet import WalletService

class TutoringService:
    """AI tutoring service using RAG for Q&A."""

    def __init__(self):
        self.rag = await create_rag_service_from_env(ai_provider="gemini")
        self.wallet = await create_wallet_service_from_env()
        self.usage_calculator = UsageCalculator(tier=PricingTier.BASIC)

    async def answer_question(
        self,
        student_id: str,
        subject: str,
        question: str,
        session_id: str
    ) -> dict:
        """Answer student question using RAG."""

        # Get student and school info
        student = await db.students.find_one({"_id": ObjectId(student_id)})
        parent = await db.parents.find_one({"_id": ObjectId(student.parent_id)})
        school_id = student.school_id

        # Query RAG knowledge base
        collection_name = f"school_{school_id}_{subject.lower().replace(' ', '_')}"

        result = await self.rag.query_knowledge_base(
            collection_name=collection_name,
            query=question,
            context={
                "student_grade": student.grade,
                "student_performance": await get_student_performance(student_id, subject),
                "preferred_explanation_style": student.learning_preferences.get("explanation_style", "standard")
            },
            filters={
                "grade": student.grade,
                "subject": subject
            },
            system_prompt_template="""
            You are Tutor Ama, a friendly and patient AI tutor helping {student_grade} students.
            Answer the student's question based on the provided study materials.

            Guidelines:
            - Use clear, simple language appropriate for {student_grade} students
            - Break down complex concepts into steps
            - Provide examples when helpful
            - Encourage the student
            - If the student seems confused, offer to explain in simpler terms
            - Always cite which part of the study material your answer comes from

            Student performance in this subject: {student_performance}
            Preferred explanation style: {preferred_explanation_style}
            """
        )

        # Calculate cost (tokens used)
        cost = self.usage_calculator.calculate_rag_cost(
            input_tokens=result.tokens_used.get("input", 500),
            output_tokens=result.tokens_used.get("output", 200),
            num_queries=1,
            provider="gemini",
            model="gemini-pro"
        )

        # Deduct from parent's wallet
        await self.wallet.debit(
            wallet_id=parent.wallet_id,
            amount=cost.total_cost,
            description=f"Tutoring: {subject} - {student.name}",
            idempotency_key=f"qa-{session_id}-{datetime.utcnow().timestamp()}",
            metadata={
                "student_id": student_id,
                "subject": subject,
                "session_id": session_id,
                "question_length": len(question),
                "answer_length": len(result.answer)
            }
        )

        # Log interaction
        await db.tutoring_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {
                    "interactions": {
                        "question": question,
                        "answer": result.answer,
                        "confidence": result.confidence,
                        "sources": result.sources,
                        "cost": float(cost.total_cost),
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )

        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": result.sources,
            "cost": float(cost.total_cost),
            "remaining_balance": float(await self.wallet.get_balance(parent.wallet_id))
        }
```

**Advanced: Voice Tutoring with VAPI (Optional):**

```python
from apps.shared.integration.vapi import VAPIService

vapi = VAPIService()

# Create conversational AI tutor
tutor_assistant = await vapi.create_assistant(
    name="Tutor Ama - Science Tutor",
    first_message="Hi {{student.name}}! I'm Tutor Ama, your Science tutor. What would you like to learn today?",
    model="gpt-4o",
    voice="jennifer",
    server_url="https://edumate.kasaai.ailabsafrica.com/api/v1/vapi/webhook",
    functions=[
        {
            "name": "answer_from_knowledge_base",
            "description": "Search study materials to answer student's question",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "subject": {"type": "string"},
                    "topic": {"type": "string"}
                }
            }
        },
        {
            "name": "give_exercise",
            "description": "Generate practice exercise for student",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]}
                }
            }
        },
        {
            "name": "evaluate_answer",
            "description": "Evaluate student's answer to exercise",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "student_answer": {"type": "string"},
                    "correct_answer": {"type": "string"}
                }
            }
        }
    ]
)

# Start voice tutoring session
call = await vapi.create_web_call(
    assistant_id=tutor_assistant.id,
    metadata={
        "student_id": str(student.id),
        "subject": "Science",
        "grade": student.grade,
        "session_id": session_id
    }
)
```

**Database Schema:**
```python
TutoringSession:
  - id: ObjectId
  - student_id: ObjectId (ref: Student)
  - subject: str
  - start_time: datetime
  - end_time: datetime (optional)
  - interactions: List[dict]  # Question/answer pairs
  - total_cost: Decimal
  - status: str  # "active", "completed"
  - created_at: datetime

StudentProgress:
  - id: ObjectId
  - student_id: ObjectId (ref: Student)
  - subject: str
  - topic: str
  - questions_asked: int
  - exercises_completed: int
  - average_score: float
  - time_spent_minutes: int
  - last_session: datetime
  - created_at: datetime
  - updated_at: datetime
```

---

### 4. **Practice Exercises & Feedback**

**Features:**
- Auto-generated exercises from study materials
- Multiple question types (MCQ, short answer, essay)
- Instant feedback with explanations
- Adaptive difficulty based on performance
- Exercise history and analytics

**Exercise Generation with RAG:**
```python
class ExerciseService:
    """Generate and evaluate practice exercises."""

    def __init__(self):
        self.rag = await create_rag_service_from_env(ai_provider="gemini")

    async def generate_exercise(
        self,
        student_id: str,
        subject: str,
        topic: str,
        difficulty: str,
        num_questions: int = 5
    ) -> dict:
        """Generate practice exercise using RAG."""

        student = await db.students.find_one({"_id": ObjectId(student_id)})
        school_id = student.school_id
        collection_name = f"school_{school_id}_{subject.lower().replace(' ', '_')}"

        # Query RAG to generate questions
        result = await self.rag.query_knowledge_base(
            collection_name=collection_name,
            query=f"Generate {num_questions} {difficulty} practice questions about {topic}",
            context={
                "task": "generate_exercise",
                "student_grade": student.grade,
                "difficulty": difficulty,
                "num_questions": num_questions
            },
            filters={
                "topic": topic,
                "difficulty": difficulty
            },
            system_prompt_template="""
            You are an educational content creator. Generate {num_questions} multiple-choice questions
            about {topic} for {student_grade} students at {difficulty} difficulty level.

            Format:
            Question 1: [question text]
            A) [option]
            B) [option]
            C) [option]
            D) [option]
            Correct Answer: [A/B/C/D]
            Explanation: [why this is correct]

            Make questions engaging and test understanding, not just memorization.
            """
        )

        # Parse questions from AI response
        questions = self._parse_questions(result.answer)

        # Store exercise
        exercise = await db.exercises.insert_one({
            "student_id": ObjectId(student_id),
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "status": "pending",
            "created_at": datetime.utcnow()
        })

        return {"exercise_id": str(exercise.inserted_id), "questions": questions}

    async def evaluate_exercise(
        self,
        exercise_id: str,
        student_answers: List[str]
    ) -> dict:
        """Evaluate student's exercise submission."""

        exercise = await db.exercises.find_one({"_id": ObjectId(exercise_id)})

        # Calculate score
        correct_count = 0
        feedback = []

        for i, (question, student_answer) in enumerate(zip(exercise["questions"], student_answers)):
            is_correct = student_answer == question["correct_answer"]
            if is_correct:
                correct_count += 1

            feedback.append({
                "question_number": i + 1,
                "is_correct": is_correct,
                "student_answer": student_answer,
                "correct_answer": question["correct_answer"],
                "explanation": question["explanation"]
            })

        score = (correct_count / len(exercise["questions"])) * 100

        # Update exercise
        await db.exercises.update_one(
            {"_id": ObjectId(exercise_id)},
            {
                "$set": {
                    "student_answers": student_answers,
                    "score": score,
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }
            }
        )

        # Update student progress
        await update_student_progress(
            exercise["student_id"],
            exercise["subject"],
            exercise["topic"],
            score
        )

        return {
            "score": score,
            "feedback": feedback,
            "performance_message": generate_performance_message(score)
        }

def generate_performance_message(score: float) -> str:
    """Generate encouraging message based on score."""
    if score >= 90:
        return "Excellent work! You've mastered this topic! 🌟"
    elif score >= 80:
        return "Great job! You're doing really well! 👏"
    elif score >= 70:
        return "Good effort! Keep practicing to improve! 💪"
    elif score >= 60:
        return "You're getting there! Review the explanations and try again. 📚"
    else:
        return "Don't worry! Let's go over this topic again together. You've got this! 💙"
```

---

### 5. **Parent Dashboard & Reports**

**Features:**
- Real-time wallet balance and transaction history
- Weekly AI-generated progress reports
- Time spent per subject analytics
- Strengths and weak areas identification
- Spending controls (daily/weekly limits)
- Usage alerts (low balance, excessive usage)

**Weekly Report Generation:**
```python
class ReportService:
    """Generate AI-powered progress reports for parents."""

    def __init__(self):
        self.rag = await create_rag_service_from_env(ai_provider="gemini")

    async def generate_weekly_report(
        self,
        student_id: str,
        week_start: datetime,
        week_end: datetime
    ) -> dict:
        """Generate comprehensive weekly progress report."""

        # Gather data
        sessions = await db.tutoring_sessions.find({
            "student_id": ObjectId(student_id),
            "created_at": {"$gte": week_start, "$lte": week_end}
        }).to_list(None)

        exercises = await db.exercises.find({
            "student_id": ObjectId(student_id),
            "created_at": {"$gte": week_start, "$lte": week_end},
            "status": "completed"
        }).to_list(None)

        # Calculate statistics
        stats = {
            "total_time_minutes": sum(
                (s["end_time"] - s["start_time"]).total_seconds() / 60
                for s in sessions if s.get("end_time")
            ),
            "questions_asked": sum(len(s["interactions"]) for s in sessions),
            "exercises_completed": len(exercises),
            "average_score": statistics.mean([e["score"] for e in exercises]) if exercises else 0,
            "subjects_studied": list(set(s["subject"] for s in sessions)),
            "total_cost": sum(s["total_cost"] for s in sessions)
        }

        # Performance by subject
        subject_performance = {}
        for subject in stats["subjects_studied"]:
            subject_exercises = [e for e in exercises if e["subject"] == subject]
            subject_performance[subject] = {
                "exercises_completed": len(subject_exercises),
                "average_score": statistics.mean([e["score"] for e in subject_exercises]) if subject_exercises else 0,
                "topics_covered": list(set(e["topic"] for e in subject_exercises))
            }

        # Generate AI summary and recommendations
        result = await self.rag.query_knowledge_base(
            collection_name="educational_insights",
            query=f"Generate insights and recommendations based on student performance data",
            context={
                "statistics": stats,
                "subject_performance": subject_performance
            },
            system_prompt_template="""
            You are an educational analyst generating a weekly progress report for parents.

            Based on the student's performance data, provide:
            1. Overall summary (2-3 sentences)
            2. Strengths (what the student is doing well)
            3. Areas for improvement (what needs more focus)
            4. Specific recommendations (actionable tips for parents)

            Be encouraging and constructive. Focus on growth and learning.
            """
        )

        # Store report
        report = await db.progress_reports.insert_one({
            "student_id": ObjectId(student_id),
            "week_start": week_start,
            "week_end": week_end,
            "statistics": stats,
            "subject_performance": subject_performance,
            "ai_summary": result.answer,
            "generated_at": datetime.utcnow()
        })

        # Send notification to parent
        await send_report_notification(student_id, report.inserted_id)

        return {
            "report_id": str(report.inserted_id),
            "statistics": stats,
            "subject_performance": subject_performance,
            "ai_summary": result.answer
        }
```

**Database Schema:**
```python
ProgressReport:
  - id: ObjectId
  - student_id: ObjectId (ref: Student)
  - week_start: datetime
  - week_end: datetime
  - statistics: dict  # Time, questions, exercises, scores
  - subject_performance: dict  # Per-subject breakdown
  - ai_summary: str
  - generated_at: datetime
  - viewed_by_parent: bool
  - viewed_at: datetime (optional)
```

---

### 6. **Wallet & Billing System**

**Features:**
- Parent-controlled wallet for each student
- Top-up via MoMo, Paystack, Stripe
- Real-time cost deduction per interaction
- Usage limits (daily/weekly spending caps)
- Low-balance alerts
- Refund support

**Pricing Table:**

| Tier | Description | Cost |
|------|-------------|------|
| **Free Trial** | 30 minutes of tutoring | Free |
| **Pay-as-you-learn** | Top-up as needed | ₵20 = 100 minutes |
| **Monthly Plan** | Unlimited tutoring | ₵50/month per student |
| **School Plan** | Bulk pricing for schools | ₵30/month per student (min 50 students) |

**Implementation:**
```python
from apps.shared.integration.wallet import WalletService, create_wallet_service_from_env
from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier

# Initialize services
wallet_service = await create_wallet_service_from_env()
usage_calculator = UsageCalculator(tier=PricingTier.BASIC)

# Create wallet for parent
parent_wallet = await wallet_service.create_wallet(
    user_id=str(parent.id),
    currency="GHS",
    initial_balance=Decimal("20.00")  # Welcome bonus
)

# Top-up via Paystack
payment = await wallet_service.initiate_paystack_topup(
    wallet_id=parent_wallet.wallet_id,
    amount=Decimal("100.00"),
    email=parent.email,
    callback_url="https://edumate.kasaai.ailabsafrica.com/wallet/callback"
)

# Deduct cost per tutoring interaction
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
    allow_negative=False,  # Block if insufficient balance
    metadata={
        "student_id": str(student.id),
        "subject": subject,
        "session_id": session_id
    }
)

# Check balance and alert if low
balance = await wallet_service.get_balance(parent_wallet.wallet_id)
if balance < Decimal("10.00"):
    await send_low_balance_alert(parent.id, balance)
```

---

## 📱 Mobile App Structure

### Navigation

```
TabNavigator:
├── Home
│   ├── Active subjects
│   ├── Today's learning stats
│   ├── Continue learning card
│   └── Achievement badges
├── Subjects
│   ├── Subject list
│   ├── Subject details
│   │   ├── Topics
│   │   ├── Ask question
│   │   ├── Take exercise
│   │   └── Progress
├── Exercises
│   ├── Available exercises
│   ├── Exercise details
│   ├── Take exercise
│   └── Review past exercises
├── Progress
│   ├── Overall stats
│   ├── Subject breakdown
│   ├── Recent activity
│   └── Achievements
└── Profile
    ├── Personal info
    ├── Learning preferences
    └── Voice settings
```

---

## 🔐 Security & Privacy

### Authentication
- Multi-factor authentication (phone + email verification)
- JWT tokens for API authentication
- Session management via Supabase
- Role-based access control (Student, Parent, Teacher, Admin)

### Data Privacy
- Student learning data encrypted at rest
- Minimal data collection (name, email, grade)
- COPPA/GDPR compliant
- Parent consent for students under 13
- Data export/deletion on request

### API Security
- HTTPS only
- Rate limiting on endpoints
- Input validation and sanitization
- MongoDB injection prevention
- CORS configuration

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                   Users                         │
│  (Mobile App + Web Portals)                     │
└──────────────────┬──────────────────────────────┘
                   │
                   │ HTTPS
                   │
┌──────────────────▼──────────────────────────────┐
│          Nginx Reverse Proxy                    │
│      edumate.kasaai.ailabsafrica.com            │
└──────────────────┬──────────────────────────────┘
                   │
                   │
┌──────────────────▼──────────────────────────────┐
│        FastAPI Backend (Python)                 │
│    - REST API                                   │
│    - Business Logic                             │
│    - Integration Layer                          │
└──────┬──────────┬──────────┬───────────────────┘
       │          │          │
       │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌──▼─────────────┐
  │MongoDB │ │Postgres│ │Shared Services │
  │        │ │pgvector│ │(RAG, Wallet,   │
  │        │ │        │ │DocumentProc)   │
  └────────┘ └────────┘ └────────────────┘
```

**Services:**
- Backend API: systemd service `kasaai-edumate.service`
- Nginx config: `edumate.kasaai.ailabsafrica.com.conf`
- MongoDB: Existing KasaAI MongoDB instance
- PostgreSQL: Existing KasaAI PostgreSQL instance (for pgvector)

---

## 🎯 Development Principles

### Code Quality
- Follow PEP 8 for Python, ESLint/Prettier for JavaScript/TypeScript
- Type hints everywhere (Python), TypeScript for frontend
- Maximum 500 lines per file
- Comprehensive docstrings (Google style)
- Unit tests for all business logic (pytest)
- Integration tests for API endpoints

### File Structure
```
/opt/kasaai/apps/personal_tutor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── materials.py
│   │   │   │   ├── tutoring.py
│   │   │   │   ├── exercises.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── wallet.py
│   │   │   │   └── vapi.py (optional)
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── student.py
│   │   │   ├── material.py
│   │   │   ├── session.py
│   │   │   └── exercise.py
│   │   ├── schemas/
│   │   │   └── (Pydantic models for API)
│   │   ├── services/
│   │   │   ├── tutoring_service.py
│   │   │   ├── exercise_service.py
│   │   │   ├── report_service.py
│   │   │   └── material_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_tutoring.py
│   │   ├── test_exercises.py
│   │   └── test_reports.py
│   ├── requirements.txt
│   └── .env
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   ├── components/
│   │   ├── navigation/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
├── admin-portal/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
├── parent-dashboard/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
├── PLANNING.md
├── TASK.md
└── README.md
```

---

## 📊 Success Metrics

### User Engagement
- Daily active students
- Average session duration
- Questions asked per session
- Exercises completed per week
- Learning streak (consecutive days)

### Learning Outcomes
- Average exercise scores
- Score improvement over time
- Topic mastery rate
- Concept retention

### Business Metrics
- Monthly active students
- Average wallet top-up amount
- Revenue per student
- Parent satisfaction score
- School retention rate

---

## 🔮 Future Expansion

### Phase 2 Features
- Adaptive learning paths (personalized curriculum)
- Gamification (XP, badges, leaderboards, avatars)
- Peer collaboration (study groups, competitions)
- Teacher dashboard (class analytics, intervention alerts)
- Offline mode (download materials for offline study)

### Phase 3 Features
- Multi-language voice (Twi, Ga, French, Hausa)
- Video explainers integration (YouTube, custom)
- Live tutoring marketplace (connect with human tutors)
- Parent-teacher messaging
- LMS integration (Google Classroom, Moodle)

### Revenue Model
- Freemium: 30 minutes/month free trial
- Pay-as-you-learn: ₵20 = 100 minutes (most flexible)
- Monthly Plan: ₵50/month unlimited (best for regular learners)
- School Plan: ₵30/student/month (bulk discount)
- Enterprise: Custom pricing, white-label, API access

---

## 📝 Notes

- **Content quality matters:** RAG answers are only as good as uploaded materials
- **Monitor AI confidence:** Flag low-confidence answers for human review
- **Parent trust:** Weekly reports and cost transparency are critical
- **Voice quality:** Test TTS in local languages (Twi, French)
- **Offline support:** Consider cached exercises for low-connectivity regions
- **Scalability:** Design for 100,000+ students from day one

---

**Document Version History:**
- v1.0 (2025-10-24): Initial planning document created with shared services integration
